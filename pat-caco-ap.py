"""Configure on-disk files and MO2 profile for CACO + Alchemy Plus test mode Block 1 & 2."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json(
        mag_thresh=25.0,
        mag_mult=5.0,
        dur_thresh=15.0,
        dur_mult=5.0,
        impure_cost_fix=True,
    )
    apply_mode_config(
        mode_name="CACO-AP",
        caco_enabled=True,
        ap_enabled=True,
        ap_json_data=ap_json,
    )
