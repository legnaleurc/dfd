export async function handle({ event, resolve }) {
  const response = await resolve(event);

  if (response.status === 404) {
    console.warn(new Date(), response.status, event.request);
  }

  return response;
}
