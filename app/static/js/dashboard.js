document.addEventListener("DOMContentLoaded", function () {
    const dataTag = document.getElementById("dashboard-data");
    if (!dataTag) return;

    const dashboardData = JSON.parse(dataTag.textContent);

    // Category distribution
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx){
        new Chart(categoryCtx, {
            type: 'pie',
            data: {
                labels: dashboardData.category_labels,
                datasets: [{
                    label: 'Items by Category',
                    data: dashboardData.category_counts,
                    backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#3B82F6']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {position: 'bottom'}
                }
            }
        });
    }

    // price buckets
    const priceCtx = document.getElementById('priceChart');
    if (priceCtx) {
        new Chart(priceCtx, {
            type: 'bar',
            data: {
                labels: dashboardData.price_ranges,
                datasets: [{
                    label: 'Items per Price Range',
                    data: dashboardData.price_counts,
                    backgroundColor: '#6366F1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0}
                    }
                }
            }
        });
    }

    if (dashboardData.top_suppliers) {
        new Chart(document.getElementById("supplierChart"),{
            type: "doughnut",
            data: {
                labels: dashboardData.top_suppliers.map( s => s[0]),
                datasets: [{
                    label: "Top Suppliers",
                    data: dashboardData.top_suppliers.map(s => s[1]),
                    backgroundColor: ["#1E40AF", "#059669", "#D97706", "#DC2626", "#6B21A8"]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {position : "bottom"}
                }
            }

        })
    }
});