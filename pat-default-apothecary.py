"""Configure on-disk files and MO2 profile for Apothecary default prediction export."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    ap_json = build_ap_json()
    apply_mode_config(
        mode_name="Apothecary-Default",
        ap_json_data=ap_json,
        apothecary_enabled=True,
    )
    print("Next in-game command: run 'pat default apothecary'")
