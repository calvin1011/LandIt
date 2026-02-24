package main

import (
	"os"
	"strings"

	"github.com/gomutex/godocx"
	"github.com/gomutex/godocx/docx"
)

func exportCoverLetterDOCX(payload CoverLetterPayload) ([]byte, string, error) {
	doc, err := renderCoverLetterDOCX(payload)
	if err != nil {
		return nil, "", err
	}
	tmp, err := os.CreateTemp("", "landit-cl-*.docx")
	if err != nil {
		return nil, "", err
	}
	path := tmp.Name()
	tmp.Close()
	defer os.Remove(path)
	if err := doc.SaveTo(path); err != nil {
		return nil, "", err
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}
	return data, docxContentType, nil
}

func renderCoverLetterDOCX(payload CoverLetterPayload) (*docx.RootDoc, error) {
	doc, err := godocx.NewDocument()
	if err != nil {
		return nil, err
	}

	pi := payload.PersonalInfo
	name := strings.TrimSpace(pi.Name)
	if name != "" {
		p := doc.AddParagraph(name)
		p.Style("Heading 1")
	}
	contactParts := []string{}
	if pi.Email != "" {
		contactParts = append(contactParts, pi.Email)
	}
	if pi.Phone != "" {
		contactParts = append(contactParts, pi.Phone)
	}
	if pi.Location != "" {
		contactParts = append(contactParts, pi.Location)
	}
	if len(contactParts) > 0 {
		doc.AddParagraph(strings.Join(contactParts, " | ")).Style("Normal")
	}

	for _, para := range payload.Paragraphs {
		para = strings.TrimSpace(para)
		if para != "" {
			doc.AddParagraph(para).Style("Normal")
		}
	}

	return doc, nil
}
