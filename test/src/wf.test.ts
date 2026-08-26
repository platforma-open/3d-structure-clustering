import { awaitStableState, blockTest } from "@platforma-sdk/test";
// The slim facade replaced the old `blockSpec` with a from-pack-v2 pointer.
import { _3dStructureClusteringBlockPointer } from "this-block";

blockTest(
  "empty inputs — block adds cleanly and stays invalid until dataset is selected",
  { timeout: 30000 },
  async ({ rawPrj: project, expect }) => {
    const blockId = await project.addBlock(
      "3D Structure Clustering",
      _3dStructureClusteringBlockPointer,
    );
    const state = await awaitStableState(project.getBlockState(blockId), 20000);

    expect(state).toBeDefined();
    expect(state.outputs).toBeDefined();
  },
);
