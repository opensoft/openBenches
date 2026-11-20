import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import parallel
import controller

class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(memory_limit='8g', minimum_available_bytes=10*parallel.GIB,
                           parallel_capacity=dict(enabled=True, ubuntu24_workers=2))
        self.windows = dict(available=20*parallel.GIB, cpus=32, cpu_percent=10, disk_free=100*parallel.GIB)
        self.linux = dict(available=40*parallel.GIB, cpus=32, disk_free=100*parallel.GIB)
    def allowed(self, count=1):
        return parallel.admission(self.config, self.windows, self.linux, count)
    def test_healthy_second_slot_is_admitted(self):
        self.assertEqual(self.allowed(), (True,'ready'))
    def test_each_reserve_rejects_new_work(self):
        for target,key,value,reason in [
            ('windows','available',11*parallel.GIB,'windows-memory'),
            ('linux','available',17*parallel.GIB,'linux-memory'),
            ('windows','cpu_percent',70,'cpu-reserve'),
            ('linux','cpus',8,'cpu-reserve'),
            ('windows','disk_free',79*parallel.GIB,'disk-reserve'),
            ('linux','disk_free',79*parallel.GIB,'disk-reserve')]:
            with self.subTest(target=target,key=key):
                values=getattr(self,target);old=values[key];values[key]=value
                self.assertEqual(self.allowed(),(False,reason));values[key]=old
        self.assertEqual(self.allowed(2),(False,'worker-limit'))
    def test_larger_primary_memory_reserve_is_honored(self):
        self.config['minimum_available_bytes']=40*parallel.GIB
        self.assertEqual(self.allowed(),(False,'linux-memory'))
    def test_bad_measurements_fail_closed(self):
        for value in (None,float('nan'),-1,True,'20'):
            with self.subTest(value=value):
                self.windows['available']=value
                with self.assertRaises((ValueError,TypeError)):self.allowed()
        del self.linux['available']
        with self.assertRaises((ValueError,TypeError,KeyError)):self.allowed()
    def test_only_two_supported_workers_and_memory_size(self):
        self.config['parallel_capacity']['ubuntu24_workers']=3
        self.assertEqual(self.allowed(),(False,'disabled'))
        self.config['parallel_capacity']['ubuntu24_workers']=2
        self.config['memory_limit']='16g'
        self.assertEqual(self.allowed(),(False,'unsupported-worker-memory'))
    def test_engine_guard_deduplication_and_uncertain_guard_reservation(self):
        self.assertEqual(parallel.sandbox_count(['eagle-fleet-engine-a','eagle-fleet-guard-a',
            'eagle-fleet-guard-b','eagle-fleet-proxy','unrelated']),2)
    def test_cpu_delta_uses_kernel_inclusive_of_idle(self):
        self.assertEqual(parallel.cpu_load([100,200,100],[150,300,200]),75)
        with self.assertRaises(ValueError):parallel.cpu_load([1,2,3],[1,2,3])
    def test_profile_filter_preserves_existing_scope(self):
        self.config.update(pools=[{'repositories':['one/repo']}],profiles=[
            dict(labels=['eagle-linux-ubuntu24-tenant'],image='pinned'),
            dict(labels=['eagle-linux-ubuntu22'],image='other')])
        original=copy.deepcopy(self.config);result=parallel.ubuntu_config(self.config)
        self.assertEqual(result['pools'],original['pools'])
        self.assertEqual(result['profiles'],[original['profiles'][0]])
        self.assertEqual(self.config,original)
    def test_secondary_journal_never_overwrites_primary(self):
        with tempfile.TemporaryDirectory() as directory:
            primary=Path(directory)/'state.json';primary.write_text('{"phase":"listening","runner":"primary"}')
            slot=Path(directory)/'slots'/'ubuntu24-2'
            with patch.object(parallel,'SLOT',slot),patch.object(controller,'STATE',primary),patch.object(controller,'event'):
                parallel.configure_slot();controller.save({'phase':'ready'})
                self.assertEqual(json.loads(primary.read_text())['runner'],'primary')
                self.assertEqual(json.loads((slot/'state.json').read_text()),{'phase':'ready'})
    def test_recovery_precedes_stop_and_pressure(self):
        order=[]
        with patch.object(controller,'recover',side_effect=lambda:order.append('recover')), \
             patch.object(parallel,'stopped',side_effect=lambda:order.append('stop') or True), \
             patch.object(parallel,'capacity') as capacity,patch.object(controller,'execute') as execute:
            self.assertFalse(parallel.step());self.assertEqual(order,['recover','stop'])
            capacity.assert_not_called();execute.assert_not_called()
    def test_late_resource_pressure_blocks_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'config.json';config.write_text(json.dumps(dict(self.config,profiles=[dict(labels=['eagle-linux-ubuntu24'])])))
            with patch.object(controller,'CONFIG',config),patch.object(controller,'recover'), \
                 patch.object(parallel,'stopped',return_value=False),patch.object(controller,'queued',return_value=('candidate',)), \
                 patch.object(parallel,'capacity',side_effect=[True,False]),patch.object(controller,'execute') as execute:
                self.assertTrue(parallel.step());execute.assert_not_called()
    def test_drain_after_preparation_never_registers_runner(self):
        config=dict(gateway_image='gateway',backend_image='backend',memory_limit='8g',maximum_lifetime_seconds=100)
        candidate=(None,dict(organization='example',group_id=11),dict(image='pinned'),'one/repo',1,2)
        with patch.object(controller,'validate_pool'),patch.object(controller.backend,'infrastructure'), \
             patch.object(controller,'save'),patch.object(controller,'event'),patch.object(controller.backend,'create'), \
             patch.object(controller.backend,'prepare'),patch.object(controller,'api',return_value={'status':'queued'}) as api, \
             patch.object(controller,'retire',return_value=True),patch.object(controller,'cleanup'):
            controller.execute(candidate,config,drain_requested=lambda:True)
            api.assert_called_once_with('repos/one/repo/actions/jobs/2')

if __name__=='__main__':unittest.main()
