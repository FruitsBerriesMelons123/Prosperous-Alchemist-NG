"""Configure on-disk files and MO2 profile with default settings for CACO mode."""

from pat_config_helper import apply_mode_config, build_ap_json

if __name__ == "__main__":
    apply_mode_config(
        mode_name="CACO",
        caco_enabled=True,
        ap_enabled=False,
        ap_json_data=build_ap_json(),
    )
