from pack_utils import PackScenario
from uvpm_core import (Stage,
                     PackTask,
                     StageParams,
                     StdStageTarget)


class Scenario(PackScenario):

    def run(self):

        task = PackTask(0, self.pack_params)

        stage_params = StageParams()
        stage_target = StdStageTarget()

        for box in self.target_boxes:
            stage_target.append(box)

        stage = Stage()
        stage.params = stage_params
        stage.target = stage_target
        stage.input_islands = [self.islands_to_pack]
        stage.static_islands = self.static_islands

        task.add_stage(stage)
        self.pack_manager.add_task(task)

        return self.pack_manager.pack()
