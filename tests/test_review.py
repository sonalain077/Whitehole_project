import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from aie2609.classification import build_request, cache_key
from aie2609.cli import main
from aie2609.errors import ClassificationError
from aie2609.ingestion import load_news, load_universe
from aie2609.review import (REVIEW_VERSION, ReviewClassifier, build_review_request,
                            coverage_hints, load_alias_config, load_initial, review_reasons)
from tests.test_classification import sample_article, sample_universe, sample_entities, api_response
from tests.test_runner import FakeClient
from tests import requires_supplied_data


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.article = sample_article()
        self.universe = sample_universe()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_names_and_explicit_tickers_have_verbatim_hints(self):
        article = replace(self.article, headline='Apple wins.', body='Shares NASDAQ: GOOG rose. $JPM was flat.')
        hints = coverage_hints(article, self.universe)
        self.assertEqual({ticker for h in hints for ticker in h['candidate_tickers']},
                         {'AAPL', 'GOOGL', 'JPM'})
        for h in hints:
            self.assertIn(h['excerpt'], getattr(article, h['field']))
            self.assertIn(h['mention'], h['excerpt'])

    def test_common_words_do_not_match_bare_tickers_or_name_substrings(self):
        article = replace(self.article, headline='Pineapple output', body='GOOG is not a contextual listing here.')
        self.assertEqual(coverage_hints(article, self.universe), [])

    @requires_supplied_data
    def test_parenthetical_acronyms_are_not_assumed_to_be_tickers(self):
        article = replace(self.article, headline='Moving average (MA)',
                          body='Centers for Medicare services (CMS) updated a target block.')
        repo = Path(__file__).resolve().parents[1]
        hints = coverage_hints(article, load_universe(repo/'sp500.csv'))
        self.assertFalse({'MA','CMS','TGT','XYZ'} &
                         {ticker for hint in hints for ticker in hint['candidate_tickers']})

    def test_proposal_and_hints_are_data_and_change_cache_identity(self):
        initial = sample_entities()['entities']
        first = build_request(self.article, self.universe)
        review = build_review_request(self.article, self.universe, initial)
        self.assertNotEqual(cache_key(first), cache_key(review))
        self.assertEqual(review['text'], first['text'])
        self.assertEqual(review['model'], first['model'])
        self.assertNotIn('tools', review)
        self.assertIn('proposed_entities', json.loads(review['input'][-1]['content']))
        self.assertEqual(json.loads(review['input'][-1]['content'])['alias_version'],
                         'entity-aliases-v6')
        changed = build_review_request(self.article, self.universe, initial[:1])
        self.assertNotEqual(cache_key(review), cache_key(changed))

    def test_invalid_baseline_is_rejected_including_duplicate_ids(self):
        path = self.root/'baseline.json'
        row = {'id':self.article.id, 'entities':sample_entities()['entities']}
        for rows in [[row,row], [{'id':'unknown','entities':[]}], [{'id':self.article.id,'entities':[{}]}]]:
            path.write_text(json.dumps({'schema_version':1,'articles':rows}))
            with self.assertRaises(ClassificationError):
                load_initial(path, [self.article], self.universe)

    def test_review_addition_is_validated_reported_and_cached(self):
        initial = {self.article.id:sample_entities()['entities'][:1]}
        runner = ReviewClassifier(FakeClient([api_response()]), self.universe, self.root/'cache',
                                  Decimal(1), initial=initial)
        runner.run([self.article], self.root/'first', [])
        changes = json.loads((self.root/'first/review_changes.json').read_text())['articles'][0]
        self.assertEqual(changes['added'], ['JPM'])
        self.assertEqual(changes['missing_before'], ['JPM'])
        self.assertEqual(changes['review_reasons'], ['missing:JPM'])
        manifest = json.loads((self.root/'first/run_manifest.json').read_text())
        self.assertEqual(manifest['prompt_version'], REVIEW_VERSION)
        replay = ReviewClassifier(FakeClient([]), self.universe, self.root/'cache', Decimal(1), initial=initial)
        self.assertEqual(replay.run([self.article], self.root/'replay', [])['api_calls'], 0)

    def test_lexical_hint_is_not_an_automatic_addition(self):
        runner = ReviewClassifier(FakeClient([api_response({'entities':[]})]), self.universe,
                                  self.root/'cache', Decimal(1), initial={self.article.id:[]})
        runner.run([self.article], self.root/'out', [])
        result = json.loads((self.root/'out/classifications.json').read_text())
        self.assertEqual(result['articles'][0]['entities'], [])
        changes = json.loads((self.root/'out/review_changes.json').read_text())['articles'][0]
        self.assertEqual(changes['unresolved_hints_after'], ['AAPL','JPM'])

    def test_removal_and_label_change_are_flagged_without_mutating_baseline(self):
        initial = {self.article.id: sample_entities()['entities']}
        original = json.dumps(initial, sort_keys=True)
        proposed = dict(initial[self.article.id][0], label='neutral')
        runner = ReviewClassifier(FakeClient([api_response({'entities': [proposed]})]),
                                  self.universe, self.root/'cache', Decimal(1), initial=initial)
        runner.run([self.article], self.root/'out', [])
        changes = json.loads((self.root/'out/review_changes.json').read_text())['articles'][0]
        self.assertEqual(changes['removed'], ['JPM'])
        self.assertEqual(changes['unresolved_hints_after'], ['JPM'])
        self.assertEqual(changes['label_changes'],
                         [{'ticker': 'AAPL', 'before': 'positive', 'after': 'neutral'}])
        self.assertEqual(json.dumps(initial, sort_keys=True), original)

    def test_additions_only_review_rejects_removal_or_label_change(self):
        initial = {self.article.id: sample_entities()['entities']}
        proposed = dict(initial[self.article.id][0], label='neutral')
        runner = ReviewClassifier(FakeClient([api_response({'entities': [proposed]})]),
                                  self.universe, self.root/'cache', Decimal(1),
                                  initial=initial, additions_only=True, max_attempts=1)
        with self.assertRaisesRegex(ClassificationError, 'Additions-only'):
            runner.run([self.article], self.root/'out', [])

    @requires_supplied_data
    def test_versioned_aliases_find_sources_and_avoid_nasdaq_company_false_positive(self):
        repo = Path(__file__).resolve().parents[1]
        universe = load_universe(repo/'sp500.csv')
        articles = {article.id: article for article in load_news(repo/'news.json').articles}
        config = load_alias_config(universe)
        self.assertEqual(config['version'], 'entity-aliases-v6')
        configured = {ticker for row in config['aliases'] for ticker in row['tickers']}
        self.assertFalse(configured - universe.tickers)
        self.assertEqual(review_reasons(articles['N070'], [{'ticker':'JNJ'}], universe),
                         ['missing:JPM'])
        self.assertEqual(review_reasons(articles['N077'],
                         [{'ticker':'GOOGL'}, {'ticker':'NFLX'}], universe), ['missing:NWSA'])
        self.assertEqual(review_reasons(articles['N084'],
                         [{'ticker':'P'}, {'ticker':'PNR'}], universe),
                         ['ambiguous:P|PNR:Everpure'])
        self.assertNotIn('missing:NDAQ', review_reasons(articles['N003'],
                         [{'ticker':'F'}, {'ticker':'TSLA'}], universe))
        self.assertEqual(review_reasons(articles['N013'],
                         [{'ticker':'AMZN'}, {'ticker':'NWSA'}], universe), ['missing:WBD'])
        self.assertEqual(review_reasons(articles['N078'],
                         [{'ticker':'MSFT'}, {'ticker':'PEP'}, {'ticker':'TSLA'}], universe),
                         ['missing:PCAR'])
        self.assertEqual(review_reasons(articles['N082'],
                         [{'ticker':'GOOGL'}, {'ticker':'NFLX'}, {'ticker':'SPGI'},
                          {'ticker':'WFC'}], universe), ['missing:CMCSA'])

    def test_invalid_alias_configuration_is_rejected(self):
        path = self.root/'aliases.json'
        path.write_text(json.dumps({'version':'v', 'blocked_generated_names':[],
                                    'forbidden_aliases':[],
                                    'aliases':[{'names':['Alias'], 'tickers':['bad'],
                                                'type':'brand'}]}))
        with self.assertRaises(ClassificationError):
            load_alias_config(self.universe, path)

    @requires_supplied_data
    def test_cli_preview_does_not_load_key_or_make_client(self):
        path = self.root/'baseline.json'
        path.write_text(json.dumps({'schema_version':1, 'articles':[{'id':'N096','entities':[]}]}))
        repo = Path(__file__).resolve().parents[1]
        with patch('aie2609.cli.ResponsesClient') as client, patch('aie2609.cli.load_local_api_key') as key:
            with redirect_stdout(io.StringIO()):
                code = main(['review','--news',str(repo/'news.json'),'--universe',str(repo/'sp500.csv'),
                             '--classifications',str(path),'--dry-run'])
            self.assertEqual(code, 0)
            client.assert_not_called()
            key.assert_not_called()

    @requires_supplied_data
    def test_cli_preview_targets_alerts_unless_all_is_requested(self):
        repo = Path(__file__).resolve().parents[1]
        articles = {article.id: article for article in load_news(repo/'news.json').articles}
        baseline = self.root/'targeted.json'
        rows = [
            {'id':'N070', 'entities':[{'ticker':'JNJ', 'label':'positive',
                                       'evidence':articles['N070'].headline}]},
            {'id':'N077', 'entities':[{'ticker':ticker, 'label':label,
                                       'evidence':articles['N077'].headline}
                                      for ticker, label in [('GOOGL','neutral'),('NFLX','negative')]]},
            {'id':'N084', 'entities':[{'ticker':ticker, 'label':label,
                                       'evidence':articles['N084'].headline}
                                      for ticker, label in [('P','neutral'),('PNR','negative')]]},
            {'id':'N096', 'entities':[]},
        ]
        baseline.write_text(json.dumps({'schema_version':1, 'articles':rows}), encoding='utf-8')
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(['review', '--classifications', str(baseline), '--dry-run']), 0)
        targeted = json.loads(stdout.getvalue())
        self.assertEqual([row['id'] for row in targeted['articles']], ['N070', 'N077', 'N084'])
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(['review', '--classifications', str(baseline),
                                   '--dry-run', '--all']), 0)
        self.assertEqual(len(json.loads(stdout.getvalue())['articles']), 4)
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(['review', '--classifications', str(baseline),
                                   '--dry-run', '--ids', 'N096']), 0)
        self.assertEqual([row['id'] for row in json.loads(stdout.getvalue())['articles']],
                         ['N096'])
