# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt
#
# call the API from
#   /api/method/icalfeed.icalfeed.utils.calendar.download_calendar?secret=[secret]
#

from icalendar import Calendar, Event
from datetime import datetime
import frappe

def get_calendar(secret):
	# check access
	ical_sub = frappe.db.sql('''select
						secret
					from
						`tabiCal Subscription`
					where
						name = %s
					''', (secret))
	if not ical_sub:
		return
	# initialise calendar
	cal = Calendar()

	# set properties
	cal.add('prodid', '-//iCalFeed module//libracore//')
	cal.add('version', '2.0')
	#doctype is passed as an argument
	event_sub_list = frappe.db.sql('''select
								doctype_name
							from
								`tabiCal Subscription Documents`
							where
								parent = %s''',(secret), as_dict=1)

	if event_sub_list:
		events = frappe.db.sql('''select
						*
					from
						`tabEvent` 
					where
						event_type = 'Public' and name in (select parent from `tabEvent Participants` 
						where reference_doctype in (%s))'''%
						', '.join(['%s']*len(event_sub_list)), tuple([eve_sub.doctype_name for eve_sub in event_sub_list]), as_dict=1)
	else:
		events = frappe.db.sql('''select
						*
					from
						`tabEvent` ''', as_dict=1)
	# add events
	for erp_event in events:
		event = Event()
		event.add('summary', erp_event['subject'])
		event.add('dtstart', erp_event['starts_on'])
		if erp_event['ends_on']:
			event.add('dtend', erp_event['ends_on'])
		event.add('dtstamp', erp_event['modified'])
		event.add('description', erp_event['description'])
		# add to calendar
		cal.add_component(event)
	return cal

@frappe.whitelist(allow_guest=True)
def download_calendar(secret):
	frappe.local.response.filename = "calendar.ics"
	calendar = get_calendar(secret)
	if calendar:
		frappe.local.response.filecontent = calendar.to_ical()
	else:
		frappe.local.response.filecontent = "No access"
	frappe.local.response.type = "download"