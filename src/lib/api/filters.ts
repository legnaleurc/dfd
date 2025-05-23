import { RequestBuilder } from "$lib/fetch";

type ReadOnly = {
  id: number;
};
type ReadWrite = {
  regexp: string;
};

export type Filter = ReadOnly & ReadWrite;
export type MutableFilter = ReadWrite;

export function getFilterList(): RequestBuilder<Array<Filter>> {
  return new RequestBuilder<Array<Filter>>().path("/api/v1/filters");
}

export function postFilter(filter: MutableFilter): RequestBuilder<Filter> {
  return new RequestBuilder<Filter>()
    .path("/api/v1/filters")
    .post()
    .jsonBody(filter);
}

export function patchFilter(
  id: number,
  filter: MutableFilter,
): RequestBuilder<Filter> {
  return new RequestBuilder<Filter>()
    .path(`/api/v1/filters/${id}`)
    .patch()
    .jsonBody(filter);
}

export function deleteFilter(id: number): RequestBuilder<void> {
  return new RequestBuilder<void>().path(`/api/v1/filters/${id}`).delete();
}
