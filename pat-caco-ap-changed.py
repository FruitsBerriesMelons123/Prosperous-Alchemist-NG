"""Configure on-disk files and MO2 profile with changed/non-default settings for CACO+AP mode."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    apply_mode_config(
        mode_name="CACO+AP-Changed",
        caco_enabled=True,
        ap_enabled=True,
        ap_json_data=build_ap_json(
            mag_thresh=30.0,
            mag_mult=6.0,
            dur_thresh=20.0,
            dur_mult=6.0,
            impure_cost_fix=True,
        ),
    )
