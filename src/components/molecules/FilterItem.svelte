<script lang="ts">
  import { createMutation, useQueryClient } from "@tanstack/svelte-query";

  import {
    patchFilter,
    deleteFilter,
    type MutableFilter,
  } from "$lib/api/filters";
  import { enterdown } from "$lib/actions/event";
  import Icon from "$atoms/Icon.svelte";

  export let id: number;
  export let regexp: string;

  const client = useQueryClient();

  const update = createMutation({
    mutationFn: (data: MutableFilter) =>
      patchFilter(id, data).base(location.origin).fetch(),
    onSuccess: () => {
      client.invalidateQueries({
        queryKey: ["filters"],
      });
    },
  });

  const delete_ = createMutation({
    mutationFn: () => deleteFilter(id).base(location.origin).response(),
    onSuccess: () => {
      client.invalidateQueries({
        queryKey: ["filters"],
      });
    },
  });

  let line = regexp;

  $: isEmpty = !line;
  $: unchanged = line === regexp;
  $: icon = isEmpty ? "delete" : "save";

  function handleClick() {
    if (!isEmpty) {
      $update.mutate({ regexp: line });
    } else {
      $delete_.mutate();
    }
  }
</script>

<section class="flex gap-2 items-center justify-center">
  <input
    type="text"
    class="input input-bordered w-full font-mono"
    placeholder="Delete Filter"
    bind:value={line}
    use:enterdown={handleClick}
  />
  <button
    class="btn btn-square btn-outline btn-primary"
    class:btn-error={isEmpty}
    disabled={unchanged}
    on:click={handleClick}
  >
    <Icon name={icon} />
  </button>
</section>
