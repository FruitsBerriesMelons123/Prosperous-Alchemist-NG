"""Configure the MO2 profile for Ordinator default prediction export."""

from pat_config_helper import apply_mode_config, build_ap_json


if __name__ == "__main__":
	apply_mode_config(
		mode_name="Ordinator-Default",
		ap_json_data=build_ap_json(),
		ordinator_enabled=True,
	)

# Next in-game command: run 'pat default ordinator'
