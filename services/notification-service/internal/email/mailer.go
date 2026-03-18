package email

import (
	"crypto/tls"
	"log"

	"gopkg.in/gomail.v2"
)

type Mailer struct {
	dialer *gomail.Dialer
	from   string
}

func NewMailer(host string, port int, user, pass, from string) *Mailer {
	d := gomail.NewDialer(host, port, user, pass)
	d.TLSConfig = &tls.Config{InsecureSkipVerify: true} // For dev/local
	return &Mailer{dialer: d, from: from}
}

func (m *Mailer) Send(to string, subject, body string) error {
	msg := gomail.NewMessage()
	msg.SetHeader("From", m.from)
	msg.SetHeader("To", to)
	msg.SetHeader("Subject", subject)
	msg.SetBody("text/html", body)

	if err := m.dialer.DialAndSend(msg); err != nil {
		log.Printf("Failed to send email to %s: %v", to, err)
		return err
	}
	return nil
}
