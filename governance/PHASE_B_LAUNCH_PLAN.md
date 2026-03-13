# Phase B Launch Plan

**Status:** 🟢 **Ready to Launch**  
**Phase A Completion:** 2026-03-14  
**Target Launch:** 2026-03-17 (Week 2 Start)

---

## 1. Scope Expansion

| Tier | Phase A | Phase B | Change |
|------|---------|---------|--------|
| policy_change | ✅ | ✅ | Continue |
| strategic_initiative | ❌ | ✅ | **NEW** |

**strategic_initiative Definition:**
- Multi-quarter roadmap items
- Cross-functional resource allocation
- Architecture direction changes
- Vendor/partner strategic decisions

**Routing Rule:**
```
if issue_type in ["policy_change", "strategic_initiative"]:
    route_to = "Tier C"
    priority = "Standard"
    sla = "48 hours (policy) / 72 hours (strategic)"
```

---

## 2. Reviewer Roster

### Core Reviewers (4-5 trained)

| Reviewer | Tier C Certified | Specialty | Capacity |
|----------|------------------|-----------|----------|
| @reviewer-alpha | ✅ Week 1 | Operations | 3/week |
| @reviewer-beta | ⏳ Training | Engineering | 3/week |
| @reviewer-gamma | ⏳ Training | Product | 2/week |
| @reviewer-delta | ⏳ Training | Security | 2/week |
| @reviewer-epsilon | ⏳ Training | Finance | 2/week |

**Training Requirements:**
- [ ] Read REVIEWER_SOP.md
- [ ] Shadow 2 live reviews
- [ ] Co-review 2 issues with certified reviewer
- [ ] Solo review 1 issue with audit
- [ ] Certification sign-off

### Reviewer Load Balancing

```
Max per reviewer: 3 issues/week
Total capacity: 12-15 issues/week
Target volume: 10 issues/week
Buffer: 20-50%
```

---

## 3. Throughput Targets

| Metric | Phase A | Phase B | Target |
|--------|---------|---------|--------|
| Weekly volume | 5 | 10 | Max 10 |
| policy_change | 5 | 6-7 | 60-70% |
| strategic_initiative | 0 | 3-4 | 30-40% |
| Queue depth | <3 | <5 | Alert at 5 |

**Volume Ramp:**
- Week 2: 7 issues (policy 5, strategic 2)
- Week 3: 9 issues (policy 6, strategic 3)
- Week 4: 10 issues (policy 6-7, strategic 3-4)

---

## 4. Success Gates (Phase B Exit Criteria)

### 4.1 Operational Gates

| Gate | Threshold | Measurement |
|------|-----------|-------------|
| Routing accuracy | ≥95% | Weekly audit sample |
| Mean latency | <24h (policy) / <48h (strategic) | SLA tracker |
| P95 latency | <48h (policy) / <72h (strategic) | SLA tracker |
| Escalation closure rate | 100% | Follow-up tracker |

### 4.2 Quality Gates

| Gate | Threshold | Measurement |
|------|-----------|-------------|
| Review quality | >80/100 | Quality score mean |
| Rollback completeness | >80/100 | Post-decision audit |
| Conflict identification | >80/100 | Post-decision audit |
| Decision diversity | Non-single-type | Weekly distribution check |

### 4.3 Reviewer Consistency Gate (NEW)

| Gate | Threshold | Measurement |
|------|-----------|-------------|
| Inter-rater agreement | >80% | Dual-review sample |
| Calibration drift | <20% | Weekly calibration session |
| Reviewer variance | Documented | Per-reviewer quality tracking |

**Dual-Review Protocol:**
- Weekly sample: 2-3 issues
- Both reviewers independently assess
- Record: decision, rationale, quality scores
- Calculate: agreement rate, variance analysis
- Output: calibration note

---

## 5. Weekly Review Cadence

### 5.1 Standup (Daily, 5 min)

**Questions:**
1. Any issues stuck >24h?
2. Any reviewer capacity constraints?
3. Any escalations pending?
4. New strategic_initiative received?

### 5.2 Calibration Session (Weekly, 30 min)

**Attendees:** All active reviewers

**Agenda:**
1. Review dual-review sample results (10 min)
   - Agreement rate
   - Decision variance
   - Rationale divergence
2. Discuss edge cases (10 min)
   - Ambiguous policy_change
   - strategic_initiative scope boundaries
3. Align on standards (10 min)
   - Quality threshold calibration
   - Rollback rigor expectations
   - Conflict check depth

**Output:** Weekly Calibration Note

### 5.3 Phase B Review (Weekly, 45 min)

**Attendees:** Operator Lead, Reviewer Lead, Governance Council rep

**Agenda:**
1. Operational metrics (10 min)
   - Volume, latency, queue depth
2. Quality metrics (10 min)
   - Quality scores, rollback/conflict rates
3. Reviewer consistency (10 min)
   - Dual-review results, calibration status
4. Strategic_initiative patterns (10 min)
   - New decision patterns emerging
   - Scope boundary cases
5. Blockers & adjustments (5 min)

**Output:** Phase B Weekly Report

---

## 6. Calibration Protocol (NEW)

### 6.1 Dual-Review Sample Selection

**Selection Criteria:**
- 1 policy_change (routine)
- 1 policy_change (edge case)
- 1 strategic_initiative (first of type, if available)

**Randomization:**
- Random selection from weekly pool
- Balanced across reviewers
- Stratified by issue type

### 6.2 Independent Assessment

**Reviewer A:**
- Read issue (5 min)
- Assess 5 fields (5 min)
- Score rollback/conflict (5 min)
- Make 4-option decision (5 min)
- Document rationale (10 min)

**Reviewer B:** Same process, no communication

### 6.3 Agreement Calculation

| Level | Definition |
|-------|------------|
| Full agreement | Same decision + similar rationale quality |
| Decision agreement | Same decision, different rationale emphasis |
| Decision variance | Different decision categories |

**Target:** >80% decision agreement, >60% full agreement

### 6.4 Calibration Note Template

```markdown
## Week X Calibration Note

### Dual-Review Sample
| Issue | Reviewer A | Reviewer B | Agreement |
|-------|------------|------------|-----------|
| PC-XXXXX-001 | APPROVE (92) | APPROVE (88) | Full ✅ |
| PC-XXXXX-002 | REVISE (45) | REVISE (50) | Decision ✅ |
| SI-XXXXX-001 | DEFER | APPROVE | Variance 🔶 |

### Agreement Rate
- Decision agreement: 67% (2/3)
- Full agreement: 33% (1/3)

### Variance Analysis
Issue SI-XXXXX-001: Reviewer A saw risk in X, Reviewer B focused on Y.
Resolution: Agree to require explicit risk assessment for strategic_initiative.

### Calibration Actions
- [ ] Update SOP: Add risk assessment requirement
- [ ] Reviewer training: Strategic initiative risk identification

### Next Week Focus
- Monitor strategic_initiative consistency
- Re-sample SI category
```

---

## 7. Risk Mitigation

### 7.1 Volume Risk

**Risk:** 10 issues/week exceeds reviewer capacity

**Mitigation:**
- Queue alert at depth 5
- Automatic escalation to Reviewer Lead
- Emergency reviewer activation (trained backups)

### 7.2 Consistency Risk

**Risk:** Reviewer variance increases with expansion

**Mitigation:**
- Dual-review protocol catches drift early
- Weekly calibration sessions align standards
- SOP updates based on variance patterns

### 7.3 strategic_initiative Risk

**Risk:** New type exposes undefined scope boundaries

**Mitigation:**
- First 3 strategic_initiative get dual-review mandatory
- Document scope boundary cases
- Monthly scope definition review

---

## 8. Launch Checklist

### Pre-Launch (By 2026-03-17)

- [ ] Reviewer training completed (4-5 reviewers)
- [ ] Dual-review protocol documented
- [ ] Calibration session scheduled (weekly)
- [ ] Queue alerting configured
- [ ] strategic_initiative routing tested
- [ ] Success gates baseline established

### Week 2 Launch (2026-03-17)

- [ ] 7 issues processed
- [ ] First strategic_initiative received
- [ ] First dual-review sample completed
- [ ] First calibration session held

### Week 4 Gate Review (2026-03-31)

- [ ] All success gates met
- [ ] Reviewer consistency >80%
- [ ] strategic_initiative patterns documented
- [ ] Go/No-Go to sustained operation

---

## 9. Phase B Success Definition

**Phase B COMPLETE when:**

1. Volume sustained at 10/week for 2 weeks
2. All operational gates met for 2 weeks
3. All quality gates met for 2 weeks
4. Reviewer consistency >80% for 2 weeks
5. strategic_initiative decision patterns documented
6. No critical blockers

**Then:** Declare R20 Governance Redesign **PRODUCTION READY**

---

## 10. Quick Reference

| Item | Reference |
|------|-----------|
| Reviewer SOP | `REVIEWER_SOP.md` |
| Escalation SOP | `ESCALATION_ROLLBACK_SOP.md` |
| Phase A Summary | `PHASE_A_EXEC_SUMMARY.md` |
| Weekly Review | `PHASE_B_WEEKLY_REVIEW_TEMPLATE.md` |
| Calibration Note | Section 6.4 above |

---

**Phase B Launch: 2026-03-17**  
**Target: Production Ready by 2026-03-31**
