"""Optional BeamNG.tech / BeamNGpy path — isolated, off by default."""
from __future__ import annotations


def available() -> bool:
    try:
        import beamngpy  # noqa: F401
        return True
    except ImportError:
        return False


def launch_tech(tech_home: str, level_id: str, vehicle_id: str, config_name: str) -> str:
    """Feature-flagged. Raises if beamngpy missing or tech home invalid."""
    if not available():
        raise RuntimeError("beamngpy not installed. pip install beamngpy (BeamNG.tech only).")
    from beamngpy import BeamNGpy, Scenario, Vehicle

    bng = BeamNGpy("localhost", 25252, home=tech_home)
    bng.open(launch=True)
    scenario = Scenario(level_id, "quicklaunch")
    opts = {}
    if config_name and config_name != "Default":
        opts["config"] = config_name
    veh = Vehicle("ql", model=vehicle_id, **opts)
    scenario.add_vehicle(veh)
    scenario.make(bng)
    bng.scenario.load(scenario)
    bng.scenario.start()
    return f"BeamNGpy tech session started: {level_id} / {vehicle_id}"
