import { useMemo } from "react";

import { useResourceOptions } from "@/hooks/use-resource";
import { RESOURCE_REGISTRY } from "@/components/knowledge-base/resource-configs";
import type { ReferenceMaps, ResourceKey } from "@/components/knowledge-base/types";
import { getFieldValue } from "@/components/knowledge-base/types";

/** Builds id -> label maps for a fixed set of resource keys, for rendering
 * foreign-key columns/fields as human-readable names instead of raw ids. */
export function useReferenceMaps(referenceKeys: ResourceKey[]): ReferenceMaps {
  const queries = referenceKeys.map((key) =>
    // Reference keys are a fixed, small set derived from static config, so the
    // number of hook calls never changes across renders for a given page.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useResourceOptions(key, RESOURCE_REGISTRY[key].api),
  );

  return useMemo(() => {
    const maps: ReferenceMaps = {};
    referenceKeys.forEach((key, index) => {
      const labelField = RESOURCE_REGISTRY[key].labelField;
      const items = queries[index].data?.items ?? [];
      maps[key] = new Map(
        items.map((item) => [item.id, String(getFieldValue(item, labelField))]),
      );
    });
    return maps;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [referenceKeys, ...queries.map((q) => q.data)]);
}
