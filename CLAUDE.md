# EPOS Refund System Project Notes

## HubSpot Configuration
- **Pipeline:** Revenue Team SG (`2054237899`)
- **Stage — Refund Requested:** `3730777848`
- **Stage — Refunded:** `3695886040`

## HubSpot Deal Eligible Stages (for refund form dropdown)
| Stage Name | Stage ID |
|---|---|
| Payment Collected | `3243113153` |
| Closed Won (Automated) | `3263420111` |
| Payment Verified | `3243113154` |

## HubSpot Deal "Product Info" Custom Properties
| Internal Name          | Label                   | Type     |
|------------------------|-------------------------|----------|
| `pos`                  | Retail POS $ (Software) | Currency |
| `fnb_pos`              | FnB POS $ (Software)    | Currency |
| `quantity_of_pos_sold` | Quantity of POS Sold    | Number   |
| `website`              | Website $               | Currency |
| `epos_rewards`         | EPOS Rewards $          | Currency |
| `digital_marketing`    | Digital Marketing $     | Currency |
| `hardwarepwp`          | Hardware $              | Currency |

`quantity_of_pos_sold` is metadata — not a selectable product, shown as context on POS line items.

## HubSpot Deal "Product Info" GST-Applied Properties
These are automated HubSpot properties that store post-GST values. The system uses these for all amount displays.

| Original Property  | GST-Applied Property              | Label                          |
|--------------------|-----------------------------------|--------------------------------|
| `pos`              | `retail_pos_gst_applied`          | Retail POS (GST Applied)       |
| `fnb_pos`          | `fnb_pos_gst_applied`             | FnB POS (GST Applied)          |
| `website`          | *(no GST property — use raw)*     | Website                        |
| `epos_rewards`     | `website_gst_applied`             | EPOS Rewards (GST Applied)     |
| `digital_marketing`| `digital_marketing_gst_applied`   | Digital Marketing (GST Applied)|
| `hardwarepwp`      | `hardware_gst_applied`            | Hardware (GST Applied)         |
| *(deal total)*     | `total_amount_automated_gst_applied` | Total Amount (GST Applied)  |

> Note: `website_gst_applied` is HubSpot's internal name for the EPOS Rewards GST property (naming inconsistency on HubSpot side).

## HubSpot Deal "Refund Info" Custom Properties
These are set automatically by the system on refund events:

| Internal Name       | Label               | Type            |
|---------------------|---------------------|-----------------|
| `refund_reason`     | Refund Reason       | Single-line text |
| `refund_type`       | Refund Type         | Dropdown        |
| `products_refunded` | Product(s) Refunded | Multi-line text |
| `refund_status`     | Refund Status       | Dropdown        |

### `refund_type` dropdown options
| Label   | Internal Value |
|---------|----------------|
| Full    | `Full`         |
| Partial | `Partial`      |

### `refund_status` dropdown options
| Label                    | Internal Value |
|--------------------------|----------------|
| Not Requested            | `Not Requested`|
| Requested (For BDs only) | `Requested`    |
| Under Review             | `Under Review` |
| Approved                 | `Approved`     |
| Rejected                 | `Rejected`     |
| Refunded                 | `Refunded`     |

### When each status is set automatically
| Event | `refund_status` set to |
|---|---|
| BD submits refund form | `Requested` |
| Director approves | `Under Review` |
| Director rejects | `Rejected` |
| Finance processes (manual in HubSpot) | `Approved` / `Refunded` |

## Sales Reps (HubSpot Owner IDs)
See `src/App.jsx` — SALES_REPS array.

## Colours (extracted from logo.webp)
- **Primary green:**  `#59cc53` — used as primary action colour (buttons, focus, active states)
- **Secondary blue:** `#0a21ab` — used as accent (radio dot inner colour, etc.)

## Stack
- **Frontend:** React + Vite → Vercel (`VITE_API_BASE` = Railway URL in prod)
- **Backend:** FastAPI → Railway
- **DB (local):** SQLite (`backend/refund_requests.db`)
- **Email:** Gmail SMTP + App Password
- **PDF:** ReportLab (generated at approval time)
- **Signature:** PNG image at `backend/static/signature.png`
