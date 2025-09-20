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

// Store current request data for feedback
let currentRequest = null;

document.getElementById('generate-btn').addEventListener('click', async () => {
    const question = document.getElementById('question').value;
    const sqlQueryElem = document.getElementById('sql-query');
    const resultTableBody = document.querySelector('#result-table tbody');
    const resultTableHead = document.querySelector('#result-table thead');
    const loadingElem = document.getElementById('loading');
    const queryMetrics = document.getElementById('query-metrics');
    const feedbackSection = document.getElementById('feedback-section');

    sqlQueryElem.textContent = '';
    resultTableBody.innerHTML = '';
    resultTableHead.innerHTML = '';
    queryMetrics.innerHTML = '';
    loadingElem.style.display = 'block';
    feedbackSection.style.display = 'none'; // Hide feedback section initially

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
        currentRequest = null; // Clear current request on error
    } else {
        // Store current request data for potential feedback
        currentRequest = {
            request_id: data.request_id,
            original_question: question,
            sql_query: data.sql_query,
            result: data.result,
            columns: data.columns
        };

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
        
        // Show feedback section after successful query
        feedbackSection.style.display = 'block';
        
        // Update monitoring info after successful query
        loadMonitoringInfo();
    }
});

// Handle feedback submission
document.getElementById('submit-feedback-btn').addEventListener('click', async () => {
    if (!currentRequest) {
        alert('No current request to provide feedback for.');
        return;
    }

    const feedback = document.getElementById('feedback-input').value.trim();
    if (!feedback) {
        alert('Please provide feedback before submitting.');
        return;
    }

    const sqlQueryElem = document.getElementById('sql-query');
    const resultTableBody = document.querySelector('#result-table tbody');
    const resultTableHead = document.querySelector('#result-table thead');
    const feedbackLoadingElem = document.getElementById('feedback-loading');
    const queryMetrics = document.getElementById('query-metrics');

    feedbackLoadingElem.style.display = 'block';

    try {
        const response = await fetch('/submit_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: currentRequest.request_id,
                original_question: currentRequest.original_question,
                feedback: feedback
            })
        });

        feedbackLoadingElem.style.display = 'none';
        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            // Update the display with the new results
            sqlQueryElem.textContent = data.sql_query;
            
            // Add feedback indicator to SQL query
            sqlQueryElem.textContent += '\n\n/* Generated with user feedback */';

            // Display updated query metrics
            if (data.latency && data.cost) {
                queryMetrics.innerHTML = `
                    <div class="metrics">
                        <span>✅ Feedback Applied</span> | 
                        <span>Latency: ${data.latency}s</span> | 
                        <span>Cost: $${data.cost}</span> | 
                        <span>Total Cost: $${data.total_cost}</span>
                    </div>
                `;
            }

            // Clear and repopulate table
            resultTableBody.innerHTML = '';
            resultTableHead.innerHTML = '';

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

            // Update current request with new data
            currentRequest = {
                request_id: data.request_id,
                original_question: currentRequest.original_question,
                sql_query: data.sql_query,
                result: data.result,
                columns: data.columns,
                feedback_applied: true
            };

            // Clear feedback input
            document.getElementById('feedback-input').value = '';
            
            // Update monitoring info
            loadMonitoringInfo();
        }
    } catch (error) {
        feedbackLoadingElem.style.display = 'none';
        alert(`An unexpected error occurred: ${error.toString()}`);
    }
});
