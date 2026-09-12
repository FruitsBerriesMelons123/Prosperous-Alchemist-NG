"""Configure on-disk files and MO2 profile with default settings for AP mode."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    apply_mode_config(
        mode_name="AP",
        caco_enabled=False,
        ap_enabled=True,
        ap_json_data=build_ap_json(
            mag_thresh=25.0,
            mag_mult=5.0,
            dur_thresh=15.0,
            dur_mult=5.0,
            impure_cost_fix=True,
        ),
    )
