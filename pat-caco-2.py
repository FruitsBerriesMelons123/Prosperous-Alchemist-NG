"""Configure on-disk files and MO2 profile for CACO test mode Block 3 & 4."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json()
    apply_mode_config(
        mode_name="CACO-2",
        caco_enabled=True,
        ap_enabled=False,
        ap_json_data=ap_json,
    )
