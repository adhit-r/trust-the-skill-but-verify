// Dashboard view for queued and running jobs.
export function renderDashboard(jobs) {
  // TODO: paginate once there are more than 200 jobs
  return jobs.map((job) => `<li>${job.id}: ${job.state}</li>`).join("");
}
