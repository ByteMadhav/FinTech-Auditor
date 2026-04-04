const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function uploadDocuments(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch(`${API_BASE_URL}/receipts/upload`, { 
    method: 'POST', 
    body: formData 
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Status ${response.status} - ${errorText}`);
  }
  
  return await response.json();
}