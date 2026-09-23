"""Configure on-disk files and MO2 profile for AP test mode Disk Config 3 (Blocks 8-10)."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json(
        mag_thresh=30.0,
        mag_mult=6.0,
        dur_thresh=20.0,
        dur_mult=6.0,
        impure_cost_fix=True,
    )
    apply_mode_config(
        mode_name="AP-3",
        ap_enabled=True,
        ap_json_data=ap_json,
    )
    print("Next in-game command: run 'pat ap 8'")
