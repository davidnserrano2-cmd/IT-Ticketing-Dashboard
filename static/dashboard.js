/* Counts are also rendered as HTML, so they remain available without charts. */
if (typeof Chart !== 'undefined') {
  const data = JSON.parse(document.getElementById('chart-data').textContent);
  for (const key of ['statuses', 'priorities']) {
    const canvas = document.getElementById(`${key}Chart`);
    if (!canvas) continue;
    new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data[key].map(row => row.label),
        datasets: [{label: 'Tickets', data: data[key].map(row => row.count),
          backgroundColor: ['#438cf4', '#269c89', '#d69a2e', '#8b73cc'], borderRadius: 6, maxBarThickness: 48}]
      },
      options: {responsive: true, maintainAspectRatio: false,
        plugins: {legend: {display: false}},
        scales: {y: {beginAtZero: true, ticks: {precision: 0}}, x: {grid: {display: false}}}}
    });
  }
}
