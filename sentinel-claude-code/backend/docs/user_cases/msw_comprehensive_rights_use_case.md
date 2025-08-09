Hierarchical Flow of Roles and Permissions in MSW
The MSW system employs a multi-layered approach to access control. 
Think of it like a set of nested containers, where each level defines and constrains what's possible for the levels below it.
Core Principle: A role's permissions and its effective reach (what data it can affect) are always determined by a combination of:
1.	The overarching capabilities defined at the Product (Global) Level.
2.	The configured allowances at the Community (Deployment) Level.
3.	The specific permissions assigned at the Organization Level aka Stakeholder Type Wise.
4.	The user's assigned OrganizationID and BranchID.

Step 0: Generic Admin (Global/Product Level) - Defining the Product's Overall Capabilities & Stakeholder Mapping (The Ultimate Ceiling) [e.g. Max GDP of a Country]
This is the foundational layer, where the product owner/developer defines what the MSW software can do, which business capabilities it supports, and the default mapping of these capabilities to generic Stakeholder Types.
1.This sets the absolute maximum permissible rights for any Community Admin to select from.
•	Role: Generic Admin (Global / Product Level Administrator) → System Roles
•	Actions:
o	Defines and enables Business Capabilities within the MSW product (e.g., Vessel Registration, SCN, e-PAN, Berth Planning,AC ,DC  etc.).
o	Defines generic Stakeholder Types (e.g., Shipping Agent, Port Authority, Customs, Immigration).
o	Establishes a Default Mapping / Maximum Capability Allowance for each Stakeholder Type against the defined Business Capabilities. This is the global maximum for any community or organization of that type.
•	Example:
o	The Generic Admin logs into the MSW product configuration.
o	They define and enable the "Vessel Registration Module," "SCN Module”  as Business Capabilities available in the product.
o	They define "Shipping Agent" as a Stakeholder Type.
o	For the "Shipping Agent" Stakeholder Type, they set the default capability as:
	Vessel Registration Module: (Permissions: CREATE_VESSEL_REG_REQUEST, VIEW_VESSEL_DETAILS_OWN)
	SCN Module: (Permissions: SUBMIT_SCN, VIEW_SCN_STATUS)
	Dangerous Goods Module: (Permissions: CREATE_DGD_DECLARATION)
o	They ensure that APPROVE_VESSEL_REGISTRATION is not a permission available for any Shipping Agent stakeholder but is available for a "Maritime Authority" Stakeholder Type. Do we need to do this much configuration!!
•	Flow Impact: This Step 0 sets the absolute upper limit for the entire product. No Community Admin can enable a Business Capability or grant a permission that hasn't been designed and enabled by the Generic Admin at this global level. It defines the 'menu' from which Community Admins can select.

Step 1: Community Admin (Deployment Level) - Configuring the Community's Allowed Capabilities (The Community Ceiling) → System Role
This level represents a specific instance or deployment of the MSW product for a particular region (e.g., a country). 
1.The Community Admin selects which of the globally defined Business Capabilities are available within their community and sets the Maximum Permitted Rights for Stakeholder Types within their jurisdiction, always constrained by the Generic Admin's global definitions.
•	Role: Community Admin (e.g., National Maritime Authority of India)
•	Actions:
o	Configures a specific Community (e.g., "India MSW").
o	Selects which Business Capabilities (from the list enabled by Generic Admin) are active for their community.
o	Specifies the Stakeholder Types relevant to their community.
o	Sets the Maximum Permitted Rights for each Stakeholder Type within their specific community. This can be equal to or less than the default/max set by the Generic Admin.
•	Example:
o	The Indian Maritime Authority (Community Admin) logs into the MSW system configured for India.
o	The "Vessel Registration Module," "SCN Module," and "Dangerous Goods Module" for their community (as allowed by Generic Admin).
o	They define "Shipping Agent xyz" as a Stakeholder Type == “Shipping Agent” for India.
o	For the "Shipping Agent" Stakeholder Type in India, they confirm the permissions: (CREATE_VESSEL_REG_REQUEST, SUBMIT_SCN, VIEW_VESSEL_DETAILS_OWN). They might, for example, choose not to enable CREATE_DGD_DECLARATION for Shipping Agents in India, even if Generic Admin globally permitted it.
o	They ensure that APPROVE_VESSEL_REGISTRATION is not a permission available for any Shipping Agent in India.
•	Flow Impact: This decision creates the ultimate boundary for all organizations operating within this specific community. No organization within India's MSW deployment can ever gain rights beyond what the Indian Maritime Authority has allowed for their Stakeholder Type.

Step 2: Organizational HQ Admin Defines Internal Structure & Control (Vertical Scaling)
This level represents a specific company or government body operating within the Community. 
The HQ Admin manages users and custom roles for their entire organization, always respecting the "ceiling" set by the Community Admin.
•	Role: Organizational HQ Admin (e.g., HQ Admin for "Global Shipping Inc.")
•	Actions:
o	Registers branches under their organization.
o	Appoints the Branch Admin(s) during the creation of a branch or later.
o	Defines Internal Custom Roles for their organization.
o	Assigns permissions to these custom roles, always within the limits set by the Community Admin for their Stakeholder Type.
o	Creates and manages users for HQ Branch.
•	Example:
o	"Global Shipping Inc." is registered by the admin of the company (self-registration) as a Shipping Agent Organization within the "India MSW" community. Their HQ Admin (Global Shipping Inc. Admin), also known as the HQ Admin, logs in.
o	They define new Internal Custom Roles to match their company structure. These roles are defined at the HQ Level, not at the Branch level:
	"Vessel Operations Lead" (for HQ staff)
	"Port Agent" (for HQ staff, capable of handling tasks across branches if assigned appropriate permissions like CREATE_TXN_BRANCH)
o	They assign permissions to these roles:
	To "Vessel Operations Lead": CREATE_VESSEL_REG_REQUEST, VIEW_ALL_ORG_BRANCH_DATA, CREATE_TXN_BRANCH (for any branch), MANAGE_ROLES_AND_ASSIGN_USER (for all org users).
	To "Port Agent" (HQ role): CREATE_VESSEL_REG_REQUEST, SUBMIT_SCN_TRANSACTION, VIEW_OWN_TRANSACTIONS. (Note: if this HQ "Port Agent" needs cross-branch operational abilities, they would also be assigned CREATE_TXN_BRANCH.)
o	They create users and branches:
	They create the Mumbai Branch, and during its creation, they assign Priya as the initial Branch Admin for Mumbai. Priya is also assigned the "Port Agent - Mumbai" role.
	They create the Chennai Branch, and assign Amit as the Branch Admin for Chennai. Amit is also assigned the "Port Agent - Chennai" role.
	Rahul (at HQ): Assigned "Vessel Operations Lead" role.
o	Flow Impact: The HQ Admin centralizes control, establishing the organizational structure (branches) and initial leadership (Branch Admins). Rahul, with the "Vessel Operations Lead" role, gets powerful cross-branch view/create/manage rights. Priya and Amit, as branch users and Branch Admins, get permissions relevant to their operational tasks, but their effective scope for data access and user management will be constrained to their respective branches by the system at runtime.

Step 3: The Organizational Branch Admin Manages Their Local Domain
A Branch Admin is a user within a specific branch who has been delegated limited administrative authority by the HQ Admin. Their actions are restricted to their own branch's users and roles.
•	Role: Organizational Branch Admin (e.g., Priya, Branch Admin for "Global Shipping Inc. - Mumbai")
•	Actions:
o	Creates new users only for their specific branch.
o	Defines Internal Custom Roles only for their specific branch.
o	Assigns roles to users only within their specific branch.
•	Example:
o	Priya, as the Mumbai Branch Admin, logs in.
o	She cannot see the Chennai branch in her user management view.
o	She wants to onboard a new data entry clerk. She created Deepak as a user for the Mumbai branch.
o	She assigns Deepak a role like "Mumbai Data Entry Clerk" (a custom role she might have created, or a standard branch role).
o	When creating this "Mumbai Data Entry Clerk" role, she cannot assign permissions like VIEW_ALL_ORG_BRANCH_DATA or CREATE_TXN_BRANCH to it, because those are HQ-level permissions not inherited down to the branch admin's role-creation capabilities.
o	Flow Impact: This level showcases delegated, but strictly constrained, administration. The Branch Admin ensures local operational efficiency without breaking the overall organizational or community-level controls.

Step 4: The End User Performs Operational Tasks (Runtime Enforcement)
This is where all the defined roles and scopes come into play, controlling what an individual user can actually do and see in the system based on their assigned roles and OrganizationID/BranchID.
•	Role: End User (e.g., Rahul - HQ, Priya - Mumbai Branch, Deepak - Mumbai Branch)
•	Actions: Performs day-to-day tasks based on their assigned role and dynamically enforced scope.
•	Example:
o	Rahul (HQ, "Vessel Operations Lead"):
	Logs in. When he goes to "Vessel Registration," he sees applications from all branches (Mumbai, Chennai, and HQ) due to his VIEW_ALL_ORG_BRANCH_DATA permission.
	He can edit a draft application that originated from the Chennai branch because he has a broad editing permission like EDIT_ALL_ORG_BRANCH_OPERATIONAL_DATA (assuming this permission is part of "Vessel Operations Lead").
	When he initiates a new transaction, the system might allow him to select which branch the transaction is associated with, reflecting his CREATE_TXN_BRANCH permission.
o	Priya (Mumbai Branch, "Port Agent - Mumbai"):
	Logs in. When she goes to "SCN Submissions," she only sees SCNs submitted by or for the Mumbai branch. She cannot see Chennai's SCNs (her access is blocked by her BranchID).
	When she creates a new SCN, it is automatically tagged with her OrganizationID and BranchID (Mumbai). She cannot choose another branch.
o	Deepak (Mumbai Branch, "Mumbai Data Entry Clerk"):
	Logs in. His permissions are even more specific than Priya's, strictly limited to data entry and viewing of only Mumbai branch data, as defined by Priya (Branch Admin) and constrained by the HQ Admin and Community Admin.
o	Flow Impact: Every action, every data view, is dynamically checked against the user's roles and their associated OrganizationID and BranchID. This ensures that access is precisely controlled down to the most granular level.
Use Case Analysis: Vessel Registration & Data Visibility Flow
Scenario: A user in a Shipping Agent (SA) organization registers a vessel.
Analysis Breakdown:
1.	Vessel Registration & Initial Visibility:
a.	"if a vessel is registered by a user in a branch/HQ specific in an SA organization."
i.	Permission: The user (whether in HQ or a specific branch) must possess the CREATE_VESSEL_REG_REQUEST permission, which is part of their assigned role.
ii.	Scope: When the user creates the vessel registration, the system automatically tags this transaction with their OrganizationID and their specific BranchID (or HQ's BranchID if they are an HQ user).
b.	"the vessel will be visible to the user's in that branch"
i.	How it works: Any user within that same branch (e.g., other "Port Agents" in Mumbai) who has a relevant view permission (e.g., VIEW_VESSEL_DETAILS_OWN_BRANCH, or VIEW_BRANCH_TRANSACTIONS) will be able to see this newly registered vessel. Their view is naturally scoped to their BranchID. This maintains the data silo for operational efficiency within a branch.
c.	"plus the HQ_Admin having the right to view all the transaction data across the branch."
i.	How it works: This is precisely handled by the Organizational HQ Admin role possessing the VIEW_ALL_ORG_BRANCH_DATA permission. When the HQ Admin logs in and selects any branch (including the one where the vessel was registered), they will see that vessel's registration data, along with all other transactions for that branch. Their view transcends branch silos within their organization.
2.	Branch Admin Data Isolation:
a.	"further the branch Admin can not see each other transaction data (they can'not have the view all the transaction data across the branch permission)"
i.	How it works: This is a direct and crucial enforcement of the hierarchy. A Branch Admin's role (e.g., "Port Agent - Mumbai" with Branch Admin privileges) does NOT include the VIEW_ALL_ORG_BRANCH_DATA permission. Their administrative and viewing capabilities are strictly constrained to their assigned BranchID. This prevents Mumbai's Branch Admin from seeing Chennai's operational data, maintaining internal organizational data separation.
3.	Branch Admin "Inheritance" Clarification:
a.	"Branch admin inherit the all the rights from HQ admin excpect the data visibility across all the branches."
i.	Clarification: a Branch Admin is delegated specific administrative rights by the HQ Admin (e.g., CREATE_USER for their branch, MANAGE_ROLES_AND_ASSIGN_USER for their branch users, CREATE_CUSTOM_ROLES for their branch).
ii.	The scope of these rights is constrained to their branch. They do not receive cross-branch permissions like VIEW_ALL_ORG_BRANCH_DATA, CREATE_TXN_BRANCH, or DELETE_USER/DELETE_ROLES for the entire organization, which remain exclusively with the Organizational HQ Admin.
4.	Vessel-Specific Operations and Sharing:
a.	"If a user register a vessel he can only do the further filing(operations) for that vessel like e-pan, scn , arrival and deprture clearance for that vessel."
i.	How it works: This points to a concept of transactional or object-level ownership/association. 
ii.	When a user registers a vessel, that vessel record becomes implicitly linked to them (and their branch/organization). The system's workflows would then enable subsequent operations (e.g., creating an e-Pass, SCN) only for that specific vessel, as long as the user has the relevant permission for that type of operation (e.g., CREATE_E_PAN(Pre Arrival Notification), SUBMIT_SCN). This means the permission check is: "Does user have CREATE_E_PAN(Pre Arrival Notification) for this vessel?"
b.	"until vessel is shared (feature) with different shipping agent organization or within that specfic branch"
i.	"within that specific branch": If the vessel is "shared" internally within the same branch (e.g., making it accessible to all relevant users in Mumbai branch, not just the creator), it means other users with the appropriate VIEW or EDIT permissions for vessel data within that branch can now perform operations on it. This aligns with the existing branch-level data visibility.
ii.	"with different shipping agent organization": This introduces a cross-organizational sharing feature. This is a separate, more complex feature that would likely involve specific permissions for sharing out a vessel record and permissions for receiving/accessing a shared vessel record from another organization. This goes beyond the internal HQ/Branch structure of a single organization and would require explicit design.
5.	Governing Authority (Community Level) View & Action Rights:
a.	"any governing authority at the community level can have the right to view all the transaction across the community."
i.	How it works: This is consistent with the Community Admin's role (Step 1). The Community Admin possesses a top-level VIEW_ALL_COMMUNITY_TRANSACTIONS permission. This allows them to monitor all activities and data across all organizations and branches registered within their specific MSW deployment (e.g., the Indian Maritime Authority can see all vessel registrations, SCNs, etc., from all Shipping Agent organizations in India).





