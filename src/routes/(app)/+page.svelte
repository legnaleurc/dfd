<script lang="ts">
  import NewFilterItem from "$molecules/NewFilterItem.svelte";
  import FilterList from "$molecules/FilterList.svelte";
</script>

<section class="w-full flex flex-col">
  <div class="sticky-header sticky top-0 z-10 p-2 w-full flex flex-col">
    <NewFilterItem />
  </div>
  <div class="p-2 w-full flex flex-col">
    <FilterList />
  </div>
</section>

<style lang="css">
  .sticky-header {
    background-color: var(--root-bg, var(--color-base-100));
  }
</style>
