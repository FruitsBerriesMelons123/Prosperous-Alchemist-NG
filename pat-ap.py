"""Configure on-disk files and MO2 profile for AP test mode Block 1 & 2."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json(
        mag_thresh=10.0,
        mag_mult=2.0,
        dur_thresh=10.0,
        dur_mult=2.0,
        overrides={
            "Skyrim.esm|0x0003EB15": {"magnitudeThreshold": 50.0, "magnitudeMult": 10.0},
            "Skyrim.esm|0x0003EB3D": {"durationThreshold": 20.0, "durationMult": 10.0},
        },
        impure_cost_fix=False,
    )
    apply_mode_config(
        mode_name="AP",
        caco_enabled=False,
        ap_enabled=True,
        ap_json_data=ap_json,
    )
