"""Configure on-disk files and MO2 profile with changed/non-default settings for AP mode."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    apply_mode_config(
        mode_name="AP-Changed",
        caco_enabled=False,
        ap_enabled=True,
        ap_json_data=build_ap_json(
            mag_thresh=10.0,
            mag_mult=2.0,
            dur_thresh=10.0,
            dur_mult=2.0,
            impure_cost_fix=False,
            overrides={"0x0003EB15": {"magnitudeThreshold": 50.0, "magnitudeMult": 2.0}},
        ),
    )
