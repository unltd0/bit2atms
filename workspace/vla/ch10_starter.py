"""
Chapter 10 — Capstone Projects
workspace/vla/ch10_starter.py

Choose one capstone from courses/vla/ch10_capstone/README.md:
  A. Autonomous tabletop manipulation (pick & place pipeline)
  B. Language-instructed assistant (VLA + natural language interface)
  C. Multi-task imitation (train on diverse tasks, evaluate transfer)
  D. Sim-to-real benchmark (measure and close the gap systematically)

Delete the options you're not pursuing and build out your chosen one here.
"""

# ── CAPSTONE A: Autonomous tabletop manipulation ──────────────────────────
def detect_objects(image):
    """Detect and localise objects on the tabletop."""
    raise NotImplementedError

def plan_pick_place(object_poses: dict, target_location):
    """Return a sequence of (pick_pose, place_pose) tuples."""
    raise NotImplementedError

def run_pick_place_loop(robot, policy, camera, max_cycles: int = 10):
    """Full autonomous loop: detect → plan → execute → repeat."""
    raise NotImplementedError


# ── CAPSTONE B: Language-instructed assistant ────────────────────────────
def parse_instruction(text: str) -> dict:
    """Convert a natural language instruction into a structured goal."""
    raise NotImplementedError

def execute_instruction(robot, vla_policy, instruction: str):
    raise NotImplementedError


# ── CAPSTONE C: Multi-task imitation ────────────────────────────────────
TASKS = ['reach', 'push', 'pick', 'stack']

def train_multitask(task_datasets: dict, output_dir: str):
    raise NotImplementedError

def evaluate_transfer(model_path: str, held_out_task: str):
    raise NotImplementedError


# ── CAPSTONE D: Sim-to-real benchmark ───────────────────────────────────
BENCHMARK_METRICS = ['joint_rmse', 'task_success_rate', 'trajectory_smoothness']

def run_benchmark(policy, sim_env, real_robot, n_trials: int = 20) -> dict:
    raise NotImplementedError


if __name__ == '__main__':
    print('Choose your capstone and implement the relevant section above.')
