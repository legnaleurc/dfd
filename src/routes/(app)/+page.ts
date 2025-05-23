import { getFilterList } from "$lib/api/filters";
import type { PageLoad } from "./$types";

export const load = (async ({ parent, fetch, url }) => {
  const { queryClient } = await parent();

  await queryClient.prefetchQuery({
    queryKey: ["filters"],
    queryFn: () => getFilterList().use(fetch).base(url.origin).fetch(),
  });
}) satisfies PageLoad;
