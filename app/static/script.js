document.getElementById('upload-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('csv-file');
    const uploadStatus = document.getElementById('upload-status');

    if (fileInput.files.length === 0) {
        uploadStatus.textContent = 'Please select a file to upload.';
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    uploadStatus.textContent = 'Uploading and processing...';

    try {
        const response = await fetch('/upload_csv', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.textContent = `Successfully uploaded and processed '${data.filename}'. You can now query this data.`;
        } else {
            uploadStatus.textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        uploadStatus.textContent = `An unexpected error occurred: ${error.toString()}`;
    }
});

// Load monitoring info on page load
async function loadMonitoringInfo() {
    try {
        const response = await fetch('/monitoring');
        const data = await response.json();
        
        document.getElementById('cost-info').textContent = `Cost: $${data.total_cost} / $${data.cost_cap}`;
        document.getElementById('latency-info').textContent = `Avg Latency: ${data.average_latency}s`;
        document.getElementById('request-count').textContent = `Requests: ${data.total_requests}`;
    } catch (error) {
        console.error('Error loading monitoring info:', error);
    }
}

// Load monitoring info on page load
document.addEventListener('DOMContentLoaded', loadMonitoringInfo);

document.getElementById('generate-btn').addEventListener('click', async () => {
    const question = document.getElementById('question').value;
    const sqlQueryElem = document.getElementById('sql-query');
    const resultTableBody = document.querySelector('#result-table tbody');
    const resultTableHead = document.querySelector('#result-table thead');
    const loadingElem = document.getElementById('loading');
    const queryMetrics = document.getElementById('query-metrics');

    sqlQueryElem.textContent = '';
    resultTableBody.innerHTML = '';
    resultTableHead.innerHTML = '';
    queryMetrics.innerHTML = '';
    loadingElem.style.display = 'block';

    const response = await fetch('/generate_sql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question })
    });

    loadingElem.style.display = 'none';
    const data = await response.json();

    if (data.error) {
        sqlQueryElem.textContent = `Error: ${data.error}`;
    } else {
        sqlQueryElem.textContent = data.sql_query;

        // Display query metrics
        if (data.latency && data.cost) {
            queryMetrics.innerHTML = `
                <div class="metrics">
                    <span>Latency: ${data.latency}s</span> | 
                    <span>Cost: $${data.cost}</span> | 
                    <span>Total Cost: $${data.total_cost}</span>
                </div>
            `;
        }

        // Populate table header
        const headerRow = document.createElement('tr');
        data.columns.forEach(colName => {
            const th = document.createElement('th');
            th.textContent = colName;
            headerRow.appendChild(th);
        });
        resultTableHead.appendChild(headerRow);

        // Populate table body
        data.result.forEach(row => {
            const tr = document.createElement('tr');

            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            resultTableBody.appendChild(tr);
        });
        
        // Update monitoring info after successful query
        loadMonitoringInfo();
    }
});
