import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import controller


class SlotReservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.own=self.root/'state.json'
        self.other=self.root/'slots'/'ubuntu24-2'/'state.json'
        self.other.parent.mkdir(parents=True)
        self.own.write_text(json.dumps({'phase':'ready'}))
        self.other.write_text(json.dumps({'phase':'ready'}))
        self.root_patch=patch.object(controller,'ROOT',self.root)
        self.state_patch=patch.object(controller,'STATE',self.own)
        self.root_patch.start();self.addCleanup(self.root_patch.stop)
        self.state_patch.start();self.addCleanup(self.state_patch.stop)

    def select(self):
        def api(path):
            if '/jobs?' in path:
                return {'jobs':[{'id':i,'status':'queued','labels':['eagle-linux-ubuntu24'],'created_at':f'2026-10-21T00:00:0{i}Z'} for i in [9,8,7]]}
            return {'workflow_runs':[{'id':3,'created_at':'2026-10-21T00:00:00Z'}]} if 'status=queued' in path else {'workflow_runs':[]}
        config={'pools':[{'repositories':['example/project']}],'profiles':[{'labels':['eagle-linux-ubuntu24'],'image':'immutable'}]}
        with patch.object(controller,'api',side_effect=api):return controller.queued(config)

    def test_other_active_reservation_keeps_fifo_for_remaining_jobs(self):
        self.other.write_text(json.dumps({'phase':'preparing','repository':'EXAMPLE/project','job_id':7}))
        self.assertEqual(self.select()[3:],('example/project',3,8))

    def test_ready_slot_does_not_reserve_stale_metadata(self):
        self.other.write_text(json.dumps({'phase':'ready','repository':'example/project','job_id':7}))
        self.assertEqual(self.select()[5],7)

    def test_current_slot_is_not_its_own_external_reservation(self):
        self.own.write_text(json.dumps({'phase':'listening','repository':'example/project','job_id':7}))
        self.assertEqual(self.select()[5],7)

    def test_other_repository_does_not_block_same_numeric_id(self):
        self.other.write_text(json.dumps({'phase':'listening','repository':'other/project','job_id':7}))
        self.assertEqual(self.select()[5],7)

    def test_parallel_slot_symmetrically_respects_main_reservation(self):
        self.own.write_text(json.dumps({'phase':'listening','repository':'example/project','job_id':7}))
        with patch.object(controller,'STATE',self.other):self.assertEqual(self.select()[5],8)

    def test_unreadable_reservation_fails_closed_before_queue_scan(self):
        self.other.write_text('{')
        with patch.object(controller,'api') as api:
            with self.assertRaises(json.JSONDecodeError):controller.queued({'pools':[],'profiles':[]})
            api.assert_not_called()

    def test_missing_other_slot_remains_usable(self):
        self.other.unlink()
        self.assertEqual(self.select()[5],7)


    def events(self, job, completed, repository='example/project'):
        rows=[{'event':'creating','runner':f'runner-{job}','repository':repository,'job':job,'time':'2026-10-21T00:00:00Z'}]
        if completed is not None:rows.append({'event':'cleanup-verified','runner':f'runner-{job}','time':f'2026-10-21T00:00:{completed:02d}Z'})
        return rows

    def test_completed_attempt_yields_to_candidates_not_yet_dispatched(self):
        rows=self.events(7,20)
        (self.root/'events.previous.jsonl').write_text(json.dumps(rows[0])+'\n')
        (self.root/'events.jsonl').write_text(json.dumps(rows[1])+'\n')
        selected=self.select()
        self.assertEqual(selected[5],8)
        self.assertEqual(selected[0],'2026-10-21T00:00:08Z')

    def test_attempted_jobs_retry_in_order_after_other_jobs_get_a_turn(self):
        rows=sum([self.events(7,20),self.events(8,30),self.events(9,40)],[])
        (self.root/'events.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
        self.assertEqual(self.select()[5],7)

    def test_incomplete_attempt_does_not_invent_a_completed_retry(self):
        (self.root/'events.jsonl').write_text(json.dumps(self.events(7,None)[0])+'\n')
        self.assertEqual(self.select()[5],7)

    def test_other_repository_dispatch_history_does_not_change_order(self):
        (self.root/'events.jsonl').write_text('\n'.join(json.dumps(r) for r in self.events(7,20,'other/project'))+'\n')
        self.assertEqual(self.select()[5],7)


if __name__=='__main__':unittest.main()
