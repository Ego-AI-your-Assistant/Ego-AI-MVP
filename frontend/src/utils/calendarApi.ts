const API_URL = (import.meta as any).env.VITE_API_URL ?? "http://egoai.duckdns.org:8000";

function getAuthHeaders() {
  // Authentication is handled via HTTP-only cookies
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  return headers;
}

export async function fetchEvents() {
  const res = await fetch(`${API_URL}/api/v1/calendar/get_tasks`, {
    headers: getAuthHeaders(),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function createEvent(event: any) {
  // Map frontend event fields to backend expected fields
  const payload = {
    title: event.title,
    description: event.description,
    start_time: event.start || event.start_time,
    end_time: event.end || event.end_time,
    all_day: event.all_day ?? false,
    location: event.location ?? "",
    type: event.type
  };
  const res = await fetch(`${API_URL}/api/v1/calendar/set_task`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to create event");
  return res.json();
}

export async function deleteEvent(eventId: string) {
  const res = await fetch(`${API_URL}/api/v1/calendar/delete_task?event_id=${encodeURIComponent(eventId)}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete event");
  return res;
}

export async function interpretText(text: string) {
  try {
    console.log(`Calling /interpret endpoint with text: ${text}`);
    const res = await fetch(`${API_URL}/api/v1/calendar/interpret`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ text }),
      credentials: "include",
    });
    
    console.log(`/interpret response status: ${res.status}`);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error(`/interpret error response: ${errorText}`);
      throw new Error(`Failed to interpret text: ${errorText}`);
    }
    
    // Try to validate the response before returning
    try {
      // Clone the response so we can both check it and return it
      const resClone = res.clone();
      const data = await resClone.json();
      console.log("Interpret endpoint response data:", data);
      
      // Ensure the response has a valid status
      if (!data || !data.status) {
        console.error("Invalid response format from interpret endpoint:", data);
      }
    } catch (parseError) {
      console.error("Error parsing interpret response:", parseError);
      // We'll continue and let the calling code handle this
    }
    
    return res;
  } catch (error) {
    console.error("Error in interpretText:", error);
    throw error; // Re-throw the error after logging it
  }
}
