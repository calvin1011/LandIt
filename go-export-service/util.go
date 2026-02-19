package main

import "strconv"

func parseInt(s string) (int, error) {
	return strconv.Atoi(s)
}

func getTemplate(payload ExportPayload) string {
	if payload.Metadata.ATSMode {
		return "classic"
	}
	t := payload.Metadata.TemplateName
	if t == "modern" || t == "minimal" {
		return t
	}
	return "classic"
}
