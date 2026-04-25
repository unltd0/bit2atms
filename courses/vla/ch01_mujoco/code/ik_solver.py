"""
Pink IK solver on the Franka Panda. Move the end-effector to any 3D target.
"""
import numpy as np
import mujoco
import mujoco.viewer
import pink
from pink.tasks import FrameTask
import pinocchio as pin
from robot_descriptions.loaders.pinocchio import load_robot_description
import os, time as time_module

FRANKA_XML = os.path.join(os.path.dirname(__file__), "../../../../workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml")

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Troubleshooting: clone Menagerie first.")
        raise SystemExit(1)

    # Load into MuJoCo
    mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    mj_data  = mujoco.MjData(mj_model)
    mj_data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(mj_model, mj_data)

    # Load into Pink/Pinocchio for IK
    robot = load_robot_description("panda_description")
    configuration = pink.Configuration(robot.model, robot.data, robot.q0)

    # IK task: reach target position
    ee_task = FrameTask("hand", position_cost=1.0, orientation_cost=0.0)
    target = pin.SE3.Identity()
    target.translation = np.array([0.5, 0.1, 0.4])   # ← change this
    ee_task.set_target(target)

    dt = mj_model.opt.timestep

    with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
        while viewer.is_running():
            velocity = pink.solve_ik(configuration, [ee_task], dt, solver="quadprog")
            configuration.integrate_inplace(velocity, dt)
            mj_data.qpos[:7] = configuration.q[:7]   # Pinocchio q may include finger joints; take arm DOFs only
            mujoco.mj_forward(mj_model, mj_data)
            viewer.sync()
            time_module.sleep(dt)
