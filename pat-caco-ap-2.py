"""Configure on-disk files and MO2 profile for CACO + Alchemy Plus test mode Block 3 & 4."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json(
        mag_thresh=10.0,
        mag_mult=2.0,
        dur_thresh=10.0,
        dur_mult=2.0,
        impure_cost_fix=True,
    )
    apply_mode_config(
        mode_name="CACO-AP-2",
        caco_enabled=True,
        ap_enabled=True,
        ap_json_data=ap_json,
    )
