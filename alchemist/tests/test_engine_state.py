"""Engine telemetry contract tests; no observation fixtures or effect replays."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from potion_prediction_test import PlayerSettings, confirmed_settings, f32

class EngineStateTests(unittest.TestCase):
    def row(self,mode='Ordinator',engine=None):
        row=dict(mode=mode,alchemy_level='73',fortify_alchemy_level='40',alchemist_rank='0',alchemist_perk_multiplier='1',physician='0',benefactor='0',poisoner='0',purity='0',seeker_of_shadows='0')
        payload={} if engine is None else {'engine':engine}
        row['mod_settings']=json.dumps(payload)
        return row

    def engine(self):
        return dict(AlchemyIngredientInitMultiplier=5.0,AlchemySkillFactor=2.0,AlchemyPowerModifier=25.0)

    def test_independent_actor_values(self):
        player=PlayerSettings(fortify_alchemy_level=40.0,alchemy_power_modifier=25.0)
        self.assertEqual(player.alchemy_power_multiplier(),1.25)
        self.assertAlmostEqual(player.fortify_alchemy_multiplier()*player.alchemy_power_multiplier(),1.75,places=6)
        self.assertEqual(PlayerSettings().alchemy_power_multiplier(),1.0)

    def test_engine_snapshot_all_non_ap_modes(self):
        for mode in ('Vanilla','Ordinator','Requiem','Apothecary','APAFA','CACO'):
            with self.subTest(mode=mode):
                settings=confirmed_settings(self.row(mode,self.engine()),Path('synthetic'),2)
                self.assertEqual(settings.player.alchemy_level,73.0)
                self.assertEqual(settings.player.fortify_alchemy_level,40.0)
                self.assertEqual(settings.player.alchemy_power_modifier,25.0)
                self.assertEqual(settings.caco_ingredient_init_multiplier,5.0)
                self.assertEqual(settings.caco_skill_factor,2.0)
                self.assertEqual(settings.requiem_ingredient_init_multiplier,5.0)
                self.assertEqual(settings.requiem_skill_factor,2.0)

    def test_legacy_settings_readable(self):
        settings=confirmed_settings(self.row(),Path('synthetic'),2)
        self.assertEqual(settings.player.alchemy_power_modifier,0.0)
        self.assertEqual(settings.caco_ingredient_init_multiplier,4.0)
        self.assertEqual(settings.caco_skill_factor,1.5)

    def test_missing_engine_input_rejected(self):
        engine=self.engine()
        del engine['AlchemyPowerModifier']
        with self.assertRaisesRegex(ValueError,'missing engine.AlchemyPowerModifier'):
            confirmed_settings(self.row(engine=engine),Path('synthetic'),2)

    def test_invalid_snapshot_rejected(self):
        for key,value in (('AlchemyPowerModifier',float('nan')),('AlchemyIngredientInitMultiplier',0.0),('AlchemySkillFactor',float('inf'))):
            with self.subTest(key=key):
                engine=self.engine()
                engine[key]=value
                with self.assertRaises(ValueError):
                    confirmed_settings(self.row(engine=engine),Path('synthetic'),2)

if __name__=='__main__':
    unittest.main()
