package main

import (
	"testing"
)

func TestExportPDF(t *testing.T) {
	p := minimalPayload()
	data, ct, err := exportPDF(p)
	if err != nil {
		t.Fatalf("exportPDF: %v", err)
	}
	if ct != "application/pdf" {
		t.Errorf("content-type: got %q", ct)
	}
	if len(data) == 0 {
		t.Error("empty PDF")
	}
}

func TestExportDOCX(t *testing.T) {
	p := minimalPayload()
	data, ct, err := exportDOCX(p)
	if err != nil {
		t.Fatalf("exportDOCX: %v", err)
	}
	if ct != docxContentType {
		t.Errorf("content-type: got %q", ct)
	}
	if len(data) == 0 {
		t.Error("empty DOCX")
	}
}

func TestExportPreview(t *testing.T) {
	p := minimalPayload()
	data, ct, err := exportPreview(p)
	if err != nil {
		t.Fatalf("exportPreview: %v", err)
	}
	if ct != "application/json" {
		t.Errorf("content-type: got %q", ct)
	}
	if len(data) == 0 {
		t.Error("empty preview")
	}
	if !contains(data, "html") {
		t.Error("preview JSON should contain 'html' key")
	}
}

func minimalPayload() ExportPayload {
	return ExportPayload{
		PersonalInfo: PersonalInfo{
			Name:     "Test User",
			Email:    "test@example.com",
			Location: "City, ST",
		},
		Summary:        "A short summary.",
		WorkExperience: []WorkExperience{{Title: "Engineer", Company: "Acme", Bullets: []string{"Did things."}}},
		Education:      []Education{{Degree: "BS", School: "University"}},
		Skills:         map[string][]string{"Tech": {"Go", "Python"}},
		Certifications: []string{},
		Metadata:       ExportMetadata{TemplateName: "classic", ExportFormat: "pdf", ATSMode: true},
	}
}

func contains(b []byte, sub string) bool {
	for i := 0; i <= len(b)-len(sub); i++ {
		if string(b[i:i+len(sub)]) == sub {
			return true
		}
	}
	return false
}
