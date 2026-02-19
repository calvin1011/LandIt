package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

const defaultPort = "8001"
const defaultMaxConcurrent = 50

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = defaultPort
	}
	maxConcurrent := defaultMaxConcurrent
	if v := os.Getenv("MAX_CONCURRENT_EXPORTS"); v != "" {
		if n, err := parseInt(v); err == nil && n > 0 {
			maxConcurrent = n
		}
	}
	sem := make(chan struct{}, maxConcurrent)

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	http.HandleFunc("/export/pdf", exportHandler(sem, exportPDF))
	http.HandleFunc("/export/docx", exportHandler(sem, exportDOCX))
	http.HandleFunc("/export/preview", exportHandler(sem, exportPreview))

	addr := ":" + port
	log.Printf("Listening on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatal(err)
	}
}

func exportHandler(sem chan struct{}, fn func(ExportPayload) ([]byte, string, error)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		var payload ExportPayload
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}
		select {
		case sem <- struct{}{}:
			defer func() { <-sem }()
		default:
			http.Error(w, "too many concurrent exports", http.StatusServiceUnavailable)
			return
		}
		data, contentType, err := fn(payload)
		if err != nil {
			log.Printf("export error: %v", err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", contentType)
		w.Write(data)
	}
}

type ExportPayload struct {
	PersonalInfo   PersonalInfo    `json:"personal_info"`
	Summary        string          `json:"summary"`
	WorkExperience []WorkExperience `json:"work_experience"`
	Education      []Education     `json:"education"`
	Skills         map[string][]string `json:"skills"`
	Certifications []string        `json:"certifications"`
	Metadata       ExportMetadata  `json:"metadata"`
}

type PersonalInfo struct {
	Name     string `json:"name"`
	Email    string `json:"email"`
	Phone    string `json:"phone"`
	Location string `json:"location"`
	Linkedin string `json:"linkedin"`
	Github   string `json:"github"`
	Portfolio string `json:"portfolio"`
}

type WorkExperience struct {
	Title     string   `json:"title"`
	Company   string   `json:"company"`
	Location  string   `json:"location"`
	StartDate string   `json:"start_date"`
	EndDate   string   `json:"end_date"`
	IsCurrent bool     `json:"is_current"`
	Bullets   []string `json:"bullets"`
}

type Education struct {
	Degree string  `json:"degree"`
	Field  string  `json:"field"`
	School string  `json:"school"`
	GPA    *string `json:"gpa"`
	Honors *string `json:"honors"`
}

type ExportMetadata struct {
	TemplateName string `json:"template_name"`
	ExportFormat string `json:"export_format"`
	ATSMode      bool   `json:"ats_mode"`
	JobTitle     string `json:"job_title"`
}
