# Sources

## SAP fuel and procurement

Researched format: SAP S/4HANA material document/OData shape and IDoc/flat-file reality.

Useful references:

- SAP Help Portal, material document API: https://help.sap.com/docs/SAP_S4HANA_CLOUD/3f57e7df4a114edabffe8b2d581a59ed/78f5a8461d554cc38b3af2d07d6f9c8e.html
- SAP OData unit annotation guidance: https://www.sap.com/protocols/sapdata
- IDoc background: https://en.wikipedia.org/wiki/IDoc

What I learned:

- Material documents expose posting date, plant/storage location, material, quantity, and units.
- SAP OData metadata commonly links numeric quantities to unit fields.
- IDocs/flat files exist in older integrations, but their segment-level structure is heavy for a prototype.

Sample data:

`sample_data/sap_material_movements.csv` includes English headers, German-style dates, plant codes, movement types, liters, gallons, and a correction row with negative quantity.

What would break:

- Unknown material-specific unit conversions.
- Custom SAP headers or IDoc segment layouts.
- Reversal documents that should net against prior movements.

## Utility electricity

Researched format: Green Button and utility portal exports.

Useful references:

- Green Button Alliance utility bill mapping: https://www.greenbuttonalliance.org/utility-bill-data
- UtilityAPI Green Button XML docs: https://utilityapi.com/docs/greenbutton/xml
- UtilityAPI Green Button overview: https://utilityapi.com/docs/greenbutton
- Con Edison Green Button CSV/XML download description: https://www.coned.com/en/save-money/make-better-energychoices-with-green-button

What I learned:

- Utility billing data usually includes service period, usage, charges/fees, meter details, and read types.
- Green Button standardizes XML/API access, but many teams still receive CSV portal exports.
- Billing periods are account-specific and often do not align with calendar months.

Sample data:

`sample_data/utility_green_button_style.csv` includes meter IDs, service start/end dates, kWh/MWh units, tariff names, meter reads, an estimated-read marker, and a missing tariff.

What would break:

- Interval-level XML exports.
- Demand charge and tariff calculations.
- Multiple meters rolled into one bill.
- Utility-specific CSV header changes.

## Corporate travel

Researched format: Concur-style travel/expense categories and travel request segments.

Useful references:

- Concur expense category examples: https://ou.edu/content/dam/financialservices/Concur%20Travel/FSS%20-%20OU%20Expense%20Types.pdf
- Concur travel request segment examples: https://ufs.uky.edu/sites/default/files/travelrequest.pdf
- SAP Concur travel and expense overview: https://www.concur.com/travel-expense

What I learned:

- Travel rows often arrive as expense categories such as airfare, hotel, car rental, rail, parking, or ground transport.
- Flight rows may include origin and destination airport codes even when distance is absent.
- Hotel emissions need nights, while ground transport usually needs distance or spend-based fallback.

Sample data:

`sample_data/concur_travel_segments.csv` includes flights with airport codes, one flight with missing/unknown route distance, hotel nights, and ground transport miles.

What would break:

- Multi-leg trips represented as one expense.
- Cabin class adjustments.
- Rail and rental car details.
- Expense-only rows with no distance, origin, destination, or nights.
