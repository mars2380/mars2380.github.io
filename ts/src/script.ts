// Function to read and display JSON file in a table
function readJSONFileAndDisplayTable(event: Event): void {
  const fileInput = document.getElementById('jsonFileInput') as HTMLInputElement;
  const file = fileInput.files?.[0];

  if (file) {
    const reader = new FileReader();

    reader.onload = function (e: ProgressEvent<FileReader>) {
      if (e.target?.result) {
        const jsonContent = JSON.parse(e.target.result as string);
        displayDataInTable(jsonContent.users);  // Assuming the JSON has a "users" key
      }
    };

    reader.onerror = function (error) {
      console.error('Error reading file:', error);
    };

    reader.readAsText(file);
  } else {
    alert("Please select a JSON file first!");
  }
}

// Function to dynamically populate the table
function displayDataInTable(data: any[]): void {
  const tableBody = document.querySelector('#dataTable tbody');
  if (tableBody) {
    tableBody.innerHTML = '';  // Clear any existing rows

    data.forEach(user => {
      const row = document.createElement('tr');

      row.innerHTML = `
        <td>${user.id}</td>
        <td>${user.name}</td>
        <td>${user.email}</td>
        <td>${user.age}</td>
        <td>${user.active ? 'Yes' : 'No'}</td>
      `;

      tableBody.appendChild(row);
    });
  }
}

// Adding event listener to the upload button
document.getElementById('uploadButton')?.addEventListener('click', readJSONFileAndDisplayTable);
