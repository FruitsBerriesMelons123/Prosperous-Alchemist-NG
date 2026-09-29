"""Configure on-disk files and MO2 profile for APAFA (Alchemy, Potions and Food Adjustments) test mode."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json()
    apply_mode_config(
        mode_name="APAFA",
        ap_json_data=ap_json,
        apafa_enabled=True,
    )
