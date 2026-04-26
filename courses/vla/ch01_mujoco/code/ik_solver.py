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
import os
import time as time_module

FRANKA_XML = "workspace/ext/mujoco_menagerie/franka_emika_panda/scene.xml"

if __name__ == "__main__":
    if not os.path.exists(FRANKA_XML):
        print("Troubleshooting: clone Menagerie first.")
        raise SystemExit(1)

    # Load into MuJoCo
    mj_model = mujoco.MjModel.from_xml_path(FRANKA_XML)
    mj_data  = mujoco.MjData(mj_model)
    mj_data.qpos[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    mujoco.mj_forward(mj_model, mj_data)

    # Load into Pink/Pinocchio for IK (tested with pink>=0.9).
    robot = load_robot_description("panda_description")
    # Start Pinocchio at the same neutral pose as MuJoCo to avoid a jump on frame 1.
    # Franka panda_description has 9 DOF (7 arm + 2 finger); [:7] sets the arm joints.
    q0 = robot.q0.copy()
    q0[:7] = [0, -0.785, 0, -2.356, 0, 1.571, 0.785]
    configuration = pink.Configuration(robot.model, robot.data, q0)

    # IK task: reach target position.
    # "hand" is the Pinocchio frame name from panda_description — matches MuJoCo body name here.
    ee_task = FrameTask("hand", position_cost=1.0, orientation_cost=0.0)
    target = pin.SE3.Identity()
    target.translation = np.array([0.5, 0.1, 0.4])   # ← change this
    ee_task.set_target(target)

    dt = mj_model.opt.timestep

    with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
        while viewer.is_running():
            velocity = pink.solve_ik(configuration, [ee_task], dt, solver="quadprog")
            configuration.integrate_inplace(velocity, dt)
            # Pinocchio stores joint angles in .q (array-like, includes all DOFs including fingers)
            # Take the 7 arm DOFs only.
            mj_data.qpos[:7] = configuration.q[:7]
            # mj_forward (not mj_step): we're solving geometry, not simulating dynamics.
            mujoco.mj_forward(mj_model, mj_data)
            viewer.sync()
            time_module.sleep(dt)
