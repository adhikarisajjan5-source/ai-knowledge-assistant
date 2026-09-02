import { useEffect, useState } from 'react'

const HEALTH_URL = 'http://localhost:8000/health'
const DOCUMENTS_URL = 'http://localhost:8000/documents'
const ASK_URL = 'http://localhost:8000/ask'

function App() {
  const [status, setStatus] = useState('')
  const [isChecking, setIsChecking] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadMessage, setUploadMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [documents, setDocuments] = useState([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true)
  const [documentsError, setDocumentsError] = useState('')
  const [deletingDocumentId, setDeletingDocumentId] = useState(null)
  const [deleteMessage, setDeleteMessage] = useState('')
  const [question, setQuestion] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [askMessage, setAskMessage] = useState('')

  async function fetchDocuments() {
    setIsLoadingDocuments(true)
    setDocumentsError('')

    try {
      const response = await fetch(DOCUMENTS_URL)

      if (!response.ok) {
        throw new Error('Document list request failed')
      }

      const result = await response.json()
      setDocuments(result)
    } catch {
      setDocumentsError('Could not load documents.')
    } finally {
      setIsLoadingDocuments(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  async function checkBackend() {
    setIsChecking(true)
    setStatus('')

    try {
      const response = await fetch(HEALTH_URL)

      if (!response.ok) {
        throw new Error('Backend health check failed')
      }

      setStatus('Backend is online ✅')
    } catch {
      setStatus('Backend is unavailable ❌')
    } finally {
      setIsChecking(false)
    }
  }

  function handleFileChange(event) {
    setSelectedFile(event.target.files[0] ?? null)
    setUploadMessage('')
  }

  async function uploadDocument() {
    if (!selectedFile) {
      setUploadMessage('Please choose a PDF file first.')
      return
    }

    setIsUploading(true)
    setUploadMessage('')

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch(DOCUMENTS_URL, {
        method: 'POST',
        body: formData,
      })

      if (response.status === 409) {
        setUploadMessage('This document has already been uploaded.')
        return
      }

      if (!response.ok) {
        throw new Error('Document upload failed')
      }

      const result = await response.json()
      setUploadMessage(
        `Uploaded ${result.filename}: ${result.page_count} pages, ${result.chunk_count} chunks.`,
      )
      await fetchDocuments()
    } catch {
      setUploadMessage('The document could not be uploaded. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  async function deleteDocument(documentId) {
    const shouldDelete = window.confirm(
      'Are you sure you want to delete this document?',
    )

    if (!shouldDelete) {
      return
    }

    setDeletingDocumentId(documentId)
    setDeleteMessage('')

    try {
      const response = await fetch(`${DOCUMENTS_URL}/${documentId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Document deletion failed')
      }

      setDeleteMessage('Document deleted successfully.')
      await fetchDocuments()
    } catch {
      setDeleteMessage('Could not delete the document.')
    } finally {
      setDeletingDocumentId(null)
    }
  }

  async function askQuestion() {
    const trimmedQuestion = question.trim()

    if (!trimmedQuestion) {
      setAskMessage('Please enter a question.')
      return
    }

    setIsAsking(true)
    setAskMessage('')
    setAnswer('')
    setSources([])

    try {
      const response = await fetch(ASK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: trimmedQuestion }),
      })

      if (!response.ok) {
        throw new Error('Question request failed')
      }

      const result = await response.json()
      setAnswer(result.answer)
      setSources(result.sources ?? [])
    } catch {
      setAskMessage('Could not get an answer.')
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <main className="page">
      <div className="content">
        <h1>AI Knowledge Assistant</h1>

        <section className="card">
          <h2>Backend Status</h2>
          <button type="button" onClick={checkBackend} disabled={isChecking}>
            {isChecking ? 'Checking...' : 'Check Backend'}
          </button>
          {status && <p className="status" aria-live="polite">{status}</p>}
        </section>

        <section className="card">
          <h2>Upload Document</h2>
          <input type="file" accept="application/pdf,.pdf" onChange={handleFileChange} />
          <button type="button" onClick={uploadDocument} disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
          {uploadMessage && (
            <p className="status" aria-live="polite">{uploadMessage}</p>
          )}
        </section>

        <section className="card">
          <h2>Your Documents</h2>
          {isLoadingDocuments && <p>Loading documents...</p>}
          {!isLoadingDocuments && documentsError && <p>{documentsError}</p>}
          {!isLoadingDocuments && !documentsError && documents.length === 0 && (
            <p>No documents uploaded yet.</p>
          )}
          {!isLoadingDocuments && !documentsError && documents.length > 0 && (
            <ul className="document-list">
              {documents.map((document) => (
                <li key={document.id}>
                  <div className="document-details">
                    <span>{document.filename}</span>
                    <time dateTime={document.created_at}>
                      {new Date(document.created_at).toLocaleString()}
                    </time>
                  </div>
                  <button
                    className="delete-button"
                    type="button"
                    onClick={() => deleteDocument(document.id)}
                    disabled={deletingDocumentId === document.id}
                  >
                    {deletingDocumentId === document.id ? 'Deleting...' : 'Delete'}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {deleteMessage && (
            <p className="status" aria-live="polite">{deleteMessage}</p>
          )}
        </section>

        <section className="card">
          <h2>Ask Your Documents</h2>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What would you like to know?"
            rows="4"
          />
          <button type="button" onClick={askQuestion} disabled={isAsking}>
            {isAsking ? 'Thinking...' : 'Ask'}
          </button>
          {askMessage && (
            <p className="status" aria-live="polite">{askMessage}</p>
          )}
          {answer && (
            <div className="answer" aria-live="polite">
              <h3>Answer</h3>
              <p>{answer}</p>
            </div>
          )}
          {sources.length > 0 && (
            <div className="sources">
              <h3>Sources</h3>
              <ul>
                {sources.map((source, index) => (
                  <li key={`${source.filename}-${source.chunk_index}-${index}`}>
                    <span>{source.filename}</span>
                    <span>Chunk index: {source.chunk_index}</span>
                    <span>Similarity score: {source.similarity_score.toFixed(3)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}

export default App
