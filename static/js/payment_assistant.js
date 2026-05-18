/**
 * =============================================================================
 * DGD 2.0 — DGD CONSULT AU
 * AI Payment Assistant Engine
 * Location: static/js/payment_assistant.js
 *
 * Client-side intelligent payment interface with:
 * - Australian dynamic payment threshold validation
 * - BPAY, Direct Debit, Card detection & routing
 * - Real-time fee calculation with GST
 * - Transaction authorization flow
 * - Voice/keyboard hybrid interaction
 * - Accessibility-first design
 * =============================================================================
 */

(function(global) {
    'use strict';
    
    // ==========================================================================
    // CONFIGURATION — Australian Payment Landscape
    // ==========================================================================
    
    const CONFIG = {
        currency: {
            code: 'AUD',
            symbol: '$',
            locale: 'en-AU',
            minorUnit: 2
        },
        
        // Australian Regulatory Thresholds (in cents)
        thresholds: {
            card: {
                minimum: 100,              // $1.00
                maximum: 99999999,         // $999,999.99
                contactlessNoPin: 10000,   // $100.00
                dailyLimit: 1000000,       // $10,000
                singleTransaction: 5000000 // $50,000
            },
            bpay: {
                minimum: 100,
                maximum: 999999999,
                billerCodeLength: [3, 10],
                referenceLength: [1, 20]
            },
            directDebit: {
                minimum: 100,
                maximum: 99999999,
                noticeDays: 3
            },
            payId: {
                minimum: 1,
                maximum: 999999999
            }
        },
        
        // Australian Fee Structure (cents)
        fees: {
            card: {
                visaDebit: { percent: 0.55, fixed: 11, cap: 1500 },
                visaCredit: { percent: 0.89, fixed: 11, cap: 1500 },
                mastercardDebit: { percent: 0.55, fixed: 11, cap: 1500 },
                mastercardCredit: { percent: 0.89, fixed: 11, cap: 1500 },
                amex: { percent: 1.60, fixed: 10, cap: 2500 },
                diners: { percent: 2.20, fixed: 15, cap: 3500 },
                jcb: { percent: 1.40, fixed: 12, cap: 2000 },
                unionPay: { percent: 0.80, fixed: 10, cap: 1500 }
            },
            bpay: {
                flat: 88,
                percent: 0,
                gstOnFee: true
            },
            directDebit: {
                flat: 55,
                percent: 0,
                dishonourFee: 1100,
                gstOnFee: true
            },
            payId: {
                flat: 0,
                percent: 0
            }
        },
        
        gstRate: 0.10,
        
        // Service-specific pricing (cents)
        services: {
            visa_600: { base: 120000, name: 'Visitor Visa 600 Assistance' },
            visa_500: { base: 200000, name: 'Student Visa 500 Assistance' },
            visa_482: { base: 450000, name: 'TSS Visa 482 Assistance' },
            visa_186: { base: 700000, name: 'ENS Visa 186 Assistance' },
            consultation: { base: 0, name: 'Initial Consultation' },
            training_rsa: { base: 12000, name: 'RSA/RCG Certification' },
            training_whitecard: { base: 8500, name: 'White Card Certification' },
            training_agedcare: { base: 120000, name: 'Aged Care Cert III' }
        }
    };
    
    // ==========================================================================
    // UTILITY FUNCTIONS
    // ==========================================================================
    
    const Utils = {
        formatCurrency(cents) {
            return new Intl.NumberFormat(CONFIG.currency.locale, {
                style: 'currency',
                currency: CONFIG.currency.code,
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(cents / 100);
        },
        
        formatNumber(num) {
            return new Intl.NumberFormat(CONFIG.currency.locale).format(num);
        },
        
        parseAmount(input) {
            // Handle string input with currency symbols, commas
            if (typeof input === 'string') {
                const cleaned = input.replace(/[^0-9.]/g, '');
                const parsed = parseFloat(cleaned);
                return isNaN(parsed) ? 0 : Math.round(parsed * 100);
            }
            return Math.round(input);
        },
        
        validateEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },
        
        validatePhone(phone) {
            // Australian phone validation
            const cleaned = phone.replace(/[^0-9+]/g, '');
            return /^(\+61|0)[2-478]\d{8}$/.test(cleaned);
        },
        
        luhnCheck(number) {
            const clean = String(number).replace(/\D/g, '');
            if (clean.length < 13 || clean.length > 19) return false;
            
            let sum = 0;
            let isEven = false;
            
            for (let i = clean.length - 1; i >= 0; i--) {
                let digit = parseInt(clean.charAt(i), 10);
                if (isEven) {
                    digit *= 2;
                    if (digit > 9) digit -= 9;
                }
                sum += digit;
                isEven = !isEven;
            }
            
            return sum % 10 === 0;
        },
        
        detectCardType(number) {
            const patterns = {
                visa: /^4/,
                mastercard: /^5[1-5]|^2[2-7]/,
                amex: /^3[47]/,
                diners: /^3(?:0[0-5]|[68])/,
                jcb: /^35/,
                unionPay: /^62/
            };
            
            for (const [type, pattern] of Object.entries(patterns)) {
                if (pattern.test(number)) return type;
            }
            return 'unknown';
        },
        
        generateId() {
            return 'pay_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        },
        
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    };
    
    // ==========================================================================
    // VALIDATION ENGINE
    // ==========================================================================
    
    class ValidationEngine {
        static validateAmount(amountCents, method) {
            const errors = [];
            const warnings = [];
            const threshold = CONFIG.thresholds[method];
            
            if (!threshold) {
                errors.push({ code: 'METHOD_INVALID', message: 'Payment method not recognized', field: 'method' });
                return { valid: false, errors, warnings };
            }
            
            if (amountCents < threshold.minimum) {
                errors.push({
                    code: 'BELOW_MINIMUM',
                    message: `Minimum amount is ${Utils.formatCurrency(threshold.minimum)}`,
                    field: 'amount',
                    suggestion: `Enter at least ${Utils.formatCurrency(threshold.minimum)}`
                });
            }
            
            if (amountCents > threshold.maximum) {
                errors.push({
                    code: 'ABOVE_MAXIMUM',
                    message: `Maximum amount is ${Utils.formatCurrency(threshold.maximum)}`,
                    field: 'amount',
                    suggestion: `Split into multiple transactions or use bank transfer`
                });
            }
            
            // Card-specific warnings
            if (method === 'card') {
                if (amountCents > threshold.contactlessNoPin) {
                    warnings.push({
                        code: 'PIN_REQUIRED',
                        message: 'PIN entry required for this amount',
                        field: 'amount'
                    });
                }
                if (amountCents > threshold.singleTransaction) {
                    warnings.push({
                        code: 'LARGE_TRANSACTION',
                        message: 'Large transaction — additional verification may be required',
                        field: 'amount'
                    });
                }
            }
            
            return {
                valid: errors.length === 0,
                errors,
                warnings,
                canProceed: errors.length === 0
            };
        }
        
        static validateCard(cardNumber, expiryMonth, expiryYear, cvv) {
            const errors = [];
            const warnings = [];
            
            // Card number
            if (!cardNumber || cardNumber.length < 13) {
                errors.push({ code: 'CARD_SHORT', message: 'Card number too short', field: 'cardNumber' });
            } else if (!Utils.luhnCheck(cardNumber)) {
                errors.push({ code: 'CARD_INVALID', message: 'Invalid card number', field: 'cardNumber' });
            }
            
            // Expiry
            const now = new Date();
            const currentYear = now.getFullYear();
            const currentMonth = now.getMonth() + 1;
            const expYear = parseInt(expiryYear, 10);
            const expMonth = parseInt(expiryMonth, 10);
            
            if (!expYear || !expMonth || expMonth < 1 || expMonth > 12) {
                errors.push({ code: 'EXPIRY_INVALID', message: 'Invalid expiry date', field: 'expiry' });
            } else if (expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
                errors.push({ code: 'EXPIRY_PAST', message: 'Card has expired', field: 'expiry' });
            } else if (expYear > currentYear + 10) {
                warnings.push({ code: 'EXPIRY_FAR', message: 'Expiry date seems far in future', field: 'expiry' });
            }
            
            // CVV
            const cardType = Utils.detectCardType(cardNumber);
            const cvvLength = cardType === 'amex' ? 4 : 3;
            
            if (!cvv || cvv.length !== cvvLength || !/^\d+$/.test(cvv)) {
                errors.push({ 
                    code: 'CVV_INVALID', 
                    message: `CVV must be ${cvvLength} digits`, 
                    field: 'cvv' 
                });
            }
            
            return {
                valid: errors.length === 0,
                errors,
                warnings,
                cardType,
                canProceed: errors.length === 0
            };
        }
        
        static validateBPAY(billerCode, reference) {
            const errors = [];
            const { billerCodeLength, referenceLength } = CONFIG.thresholds.bpay;
            
            const bc = String(billerCode);
            if (bc.length < billerCodeLength[0] || bc.length > billerCodeLength[1]) {
                errors.push({
                    code: 'BPAY_BILLER_INVALID',
                    message: `Biller code must be ${billerCodeLength[0]}-${billerCodeLength[1]} digits`,
                    field: 'billerCode'
                });
            }
            
            const ref = String(reference);
            if (ref.length < referenceLength[0] || ref.length > referenceLength[1]) {
                errors.push({
                    code: 'BPAY_REF_INVALID',
                    message: `Reference must be ${referenceLength[0]}-${referenceLength[1]} characters`,
                    field: 'reference'
                });
            }
            
            return { valid: errors.length === 0, errors };
        }
        
        static validateDirectDebit(bsb, accountNumber, accountName) {
            const errors = [];
            
            const bsbClean = String(bsb).replace(/[^0-9]/g, '');
            if (bsbClean.length !== 6) {
                errors.push({ code: 'BSB_INVALID', message: 'BSB must be 6 digits', field: 'bsb' });
            }
            
            const accClean = String(accountNumber).replace(/[^0-9]/g, '');
            if (accClean.length < 5 || accClean.length > 9) {
                errors.push({ code: 'ACCOUNT_INVALID', message: 'Account number appears invalid', field: 'accountNumber' });
            }
            
            if (!accountName || accountName.trim().length < 2) {
                errors.push({ code: 'NAME_REQUIRED', message: 'Account name required', field: 'accountName' });
            }
            
            return { valid: errors.length === 0, errors };
        }
    }
    
    // ==========================================================================
    // FEE CALCULATION ENGINE
    // ==========================================================================
    
    class FeeEngine {
        static calculate(amountCents, method, cardType = 'visaDebit') {
            const feeConfig = CONFIG.fees[method];
            if (!feeConfig) return { merchant: 0, gst: 0, total: 0, breakdown: {} };
            
            let merchantFee = 0;
            let feeName = '';
            
            if (method === 'card') {
                const rate = feeConfig[cardType] || feeConfig.visaDebit;
                merchantFee = Math.round((amountCents * rate.percent / 100) + rate.fixed);
                merchantFee = Math.min(merchantFee, rate.cap);
                feeName = `${cardType} surcharge`;
            } else if (method === 'bpay') {
                merchantFee = feeConfig.flat;
                feeName = 'BPAY processing fee';
            } else if (method === 'directDebit') {
                merchantFee = feeConfig.flat;
                feeName = 'Direct debit processing fee';
            } else if (method === 'payId') {
                merchantFee = 0;
                feeName = 'PayID transfer';
            }
            
            const gst = Math.round(merchantFee * CONFIG.gstRate);
            const total = amountCents + merchantFee + gst;
            
            return {
                merchant: merchantFee,
                gst: gst,
                total: total,
                feeName: feeName,
                breakdown: {
                    baseAmount: amountCents,
                    merchantFee: merchantFee,
                    gstOnFee: gst,
                    grandTotal: total,
                    displayBase: Utils.formatCurrency(amountCents),
                    displayFee: Utils.formatCurrency(merchantFee),
                    displayGst: Utils.formatCurrency(gst),
                    displayTotal: Utils.formatCurrency(total)
                }
            };
        }
        
        static estimateServiceFee(serviceType, options = {}) {
            const service = CONFIG.services[serviceType];
            if (!service) return null;
            
            let baseAmount = service.base;
            
            // Apply options
            if (options.expedited) baseAmount += 50000; // +$500
            if (options.premium) baseAmount += 100000;    // +$1,000
            if (options.familyMembers) {
                baseAmount += options.familyMembers * 30000; // +$300 per member
            }
            
            return {
                serviceName: service.name,
                baseAmount: baseAmount,
                displayBase: Utils.formatCurrency(baseAmount)
            };
        }
    }
    
    // ==========================================================================
    // STATE MANAGEMENT
    // ==========================================================================
    
    class PaymentState {
        constructor() {
            this.reset();
        }
        
        reset() {
            this.transactionId = Utils.generateId();
            this.stage = 'input';        // input → validating → calculating → review → processing → complete → failed
            this.method = null;          // card | bpay | directDebit | payId
            this.amount = 0;             // cents
            this.currency = CONFIG.currency.code;
            this.cardType = null;
            this.fees = { merchant: 0, gst: 0, total: 0 };
            this.valid = false;
            this.errors = [];
            this.warnings = [];
            this.customer = {
                email: '',
                phone: '',
                name: ''
            };
            this.metadata = {};
            this.timestamp = new Date().toISOString();
        }
        
        setMethod(method) {
            this.method = method;
            this.cardType = null;
            this.recalculate();
        }
        
        setAmount(amount) {
            this.amount = Utils.parseAmount(amount);
            this.recalculate();
        }
        
        setCardType(cardNumber) {
            this.cardType = Utils.detectCardType(cardNumber);
            if (this.method === 'card') this.recalculate();
        }
        
        recalculate() {
            if (this.amount > 0 && this.method) {
                this.fees = FeeEngine.calculate(this.amount, this.method, this.cardType);
            }
        }
        
        validate() {
            if (!this.method || !this.amount) {
                return { valid: false, errors: [{ message: 'Payment method and amount required' }] };
            }
            
            const amountValidation = ValidationEngine.validateAmount(this.amount, this.method);
            this.errors = amountValidation.errors;
            this.warnings = amountValidation.warnings;
            this.valid = amountValidation.valid;
            
            return amountValidation;
        }
        
        toJSON() {
            return {
                transactionId: this.transactionId,
                stage: this.stage,
                method: this.method,
                amount: this.amount,
                currency: this.currency,
                cardType: this.cardType,
                fees: this.fees,
                valid: this.valid,
                errors: this.errors,
                warnings: this.warnings,
                customer: this.customer,
                timestamp: this.timestamp
            };
        }
    }
    
    // ==========================================================================
    // UI COMPONENT — THE AI PAYMENT ASSISTANT
    // ==========================================================================
    
    class AIPaymentAssistant {
        constructor(containerId, options = {}) {
            this.container = typeof containerId === 'string' 
                ? document.getElementById(containerId) 
                : containerId;
            
            if (!this.container) {
                throw new Error(`Payment container not found: ${containerId}`);
            }
            
            this.options = {
                serviceType: 'consultation',
                baseAmount: 0,
                currency: 'AUD',
                showFeeBreakdown: true,
                allowVoiceInput: true,
                theme: 'blue',
                onComplete: null,
                onError: null,
                ...options
            };
            
            this.state = new PaymentState();
            this.state.setAmount(this.options.baseAmount);
            
            this.elements = {};
            this.init();
        }
        
        // ---------------------------------------------------------------------
        // INITIALIZATION
        // ---------------------------------------------------------------------
        
        init() {
            this.render();
            this.bindEvents();
            this.speak('Welcome to DGD Payment Assistant. How would you like to pay?');
        }
        
        // ---------------------------------------------------------------------
        // RENDERING
        // ---------------------------------------------------------------------
        
        render() {
            const service = FeeEngine.estimateServiceFee(this.options.serviceType, this.options);
            const amountDisplay = service ? service.displayBase : Utils.formatCurrency(this.options.baseAmount);
            
            this.container.innerHTML = `
                <div class="ai-payment-widget" data-theme="${this.options.theme}">
                    <div class="payment-header">
                        <div class="payment-service">
                            <div class="payment-service-icon">💳</div>
                            <div>
                                <div class="payment-service-name">${service ? service.serviceName : 'Payment'}</div>
                                <div class="payment-service-amount" id="paymentAmount">${amountDisplay}</div>
                            </div>
                        </div>
                        <button class="payment-voice-btn" id="voiceBtn" title="Voice input">
                            <span class="voice-icon">🎤</span>
                        </button>
                    </div>
                    
                    <div class="payment-body">
                        <!-- Method Selector -->
                        <div class="payment-methods" id="methodSelector">
                            <button class="method-btn active" data-method="card" title="Credit/Debit Card">
                                <span class="method-icon">💳</span>
                                <span class="method-label">Card</span>
                            </button>
                            <button class="method-btn" data-method="bpay" title="BPAY">
                                <span class="method-icon">🏦</span>
                                <span class="method-label">BPAY</span>
                            </button>
                            <button class="method-btn" data-method="directDebit" title="Direct Debit">
                                <span class="method-icon">🔄</span>
                                <span class="method-label">Direct Debit</span>
                            </button>
                            <button class="method-btn" data-method="payId" title="PayID">
                                <span class="method-icon">⚡</span>
                                <span class="method-label">PayID</span>
                            </button>
                        </div>
                        
                        <!-- Dynamic Form Area -->
                        <div class="payment-form-area" id="formArea">
                            ${this.renderCardForm()}
                        </div>
                        
                        <!-- Fee Breakdown -->
                        <div class="payment-fees" id="feeBreakdown" style="${this.options.showFeeBreakdown ? '' : 'display:none;'}">
                            <div class="fee-row">
                                <span>Service Amount</span>
                                <span id="feeBase">${amountDisplay}</span>
                            </div>
                            <div class="fee-row">
                                <span>Processing Fee</span>
                                <span id="feeMerchant">$0.00</span>
                            </div>
                            <div class="fee-row">
                                <span>GST (10%)</span>
                                <span id="feeGst">$0.00</span>
                            </div>
                            <div class="fee-row fee-total">
                                <span>Total Amount</span>
                                <span id="feeTotal">${amountDisplay}</span>
                            </div>
                        </div>
                        
                        <!-- Validation Messages -->
                        <div class="payment-messages" id="validationMessages"></div>
                        
                        <!-- Action -->
                        <button class="payment-submit-btn" id="submitBtn" disabled>
                            <span class="submit-text">Enter payment details</span>
                            <span class="submit-loader" style="display:none;">
                                <span class="loader-dot"></span>
                                <span class="loader-dot"></span>
                                <span class="loader-dot"></span>
                            </span>
                        </button>
                        
                        <!-- Security Badges -->
                        <div class="payment-security">
                            <div class="security-badge">🔒 SSL Encrypted</div>
                            <div class="security-badge">✓ PCI DSS Compliant</div>
                            <div class="security-badge">🇦🇺 AU Regulated</div>
                        </div>
                    </div>
                    
                    <!-- Voice Overlay -->
                    <div class="voice-overlay" id="voiceOverlay" style="display:none;">
                        <div class="voice-pulse"></div>
                        <div class="voice-text">Listening...</div>
                        <div class="voice-hint">Say an amount or "pay by card"</div>
                    </div>
                </div>
            `;
            
            this.cacheElements();
        }
        
        renderCardForm() {
            return `
                <div class="form-group">
                    <label class="form-label">Card Number</label>
                    <div class="input-wrapper">
                        <input type="text" 
                               class="form-input card-number" 
                               id="cardNumber"
                               placeholder="0000 0000 0000 0000"
                               maxlength="19"
                               inputmode="numeric"
                               autocomplete="cc-number">
                        <span class="card-type-icon" id="cardTypeIcon"></span>
                    </div>
                </div>
                
                <div class="form-row-2">
                    <div class="form-group">
                        <label class="form-label">Expiry</label>
                        <input type="text" 
                               class="form-input" 
                               id="cardExpiry"
                               placeholder="MM / YY"
                               maxlength="7"
                               inputmode="numeric"
                               autocomplete="cc-exp">
                    </div>
                    <div class="form-group">
                        <label class="form-label">CVV</label>
                        <input type="text" 
                               class="form-input" 
                               id="cardCvv"
                               placeholder="123"
                               maxlength="4"
                               inputmode="numeric"
                               autocomplete="cc-csc">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Cardholder Name</label>
                    <input type="text" 
                           class="form-input" 
                           id="cardName"
                           placeholder="As shown on card"
                           autocomplete="cc-name">
                </div>
            `;
        }
        
        renderBPAYForm() {
            return `
                <div class="bpay-display">
                    <div class="bpay-logo">BPAY</div>
                    <div class="bpay-instructions">
                        Use your bank's BPAY facility to make payment
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Biller Code</label>
                    <input type="text" 
                           class="form-input" 
                           id="bpayBiller"
                           placeholder="e.g., 12345"
                           maxlength="10"
                           inputmode="numeric">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Reference Number</label>
                    <input type="text" 
                           class="form-input" 
                           id="bpayReference"
                           placeholder="Your reference"
                           maxlength="20">
                </div>
                
                <div class="bpay-note">
                    <strong>Note:</strong> Please allow 1-2 business days for BPAY payments to clear. 
                    Your service will commence upon payment confirmation.
                </div>
            `;
        }
        
        renderDirectDebitForm() {
            return `
                <div class="form-group">
                    <label class="form-label">Account Name</label>
                    <input type="text" 
                           class="form-input" 
                           id="ddName"
                           placeholder="Full account holder name">
                </div>
                
                <div class="form-group">
                    <label class="form-label">BSB</label>
                    <input type="text" 
                           class="form-input" 
                           id="ddBsb"
                           placeholder="000-000"
                           maxlength="7"
                           inputmode="numeric">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Account Number</label>
                    <input type="text" 
                           class="form-input" 
                           id="ddAccount"
                           placeholder="Account number"
                           maxlength="9"
                           inputmode="numeric">
                </div>
                
                <div class="dd-authority">
                    <label class="checkbox-label">
                        <input type="checkbox" id="ddAuthority">
                        <span>I authorize DGD CONSULT AU to debit my account for the agreed amount. 
                        I understand I will receive 3 business days notice of any changes.</span>
                    </label>
                </div>
            `;
        }
        
        renderPayIdForm() {
            return `
                <div class="payid-display">
                    <div class="payid-logo">PayID</div>
                    <div class="payid-instructions">
                        Instant payment using your bank's PayID service
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">PayID Type</label>
                    <select class="form-select" id="payIdType">
                        <option value="email">Email Address</option>
                        <option value="phone">Phone Number</option>
                        <option value="abn">ABN</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">PayID Identifier</label>
                    <input type="text" 
                           class="form-input" 
                           id="payIdValue"
                           placeholder="your@email.com or +61...">
                </div>
                
                <div class="payid-note">
                    <strong>Instant transfer:</strong> PayID payments typically clear within 60 seconds. 
                    Use the email <strong>payments@dgdconsult.com</strong> or phone <strong>+61 2 8317 5004</strong>.
                </div>
            `;
        }
        
        // ---------------------------------------------------------------------
        // EVENT BINDING
        // ---------------------------------------------------------------------
        
        cacheElements() {
            this.elements = {
                methodSelector: this.container.querySelector('#methodSelector'),
                formArea: this.container.querySelector('#formArea'),
                feeBase: this.container.querySelector('#feeBase'),
                feeMerchant: this.container.querySelector('#feeMerchant'),
                feeGst: this.container.querySelector('#feeGst'),
                feeTotal: this.container.querySelector('#feeTotal'),
                messages: this.container.querySelector('#validationMessages'),
                submitBtn: this.container.querySelector('#submitBtn'),
                voiceBtn: this.container.querySelector('#voiceBtn'),
                voiceOverlay: this.container.querySelector('#voiceOverlay'),
                cardTypeIcon: this.container.querySelector('#cardTypeIcon')
            };
        }
        
        bindEvents() {
            // Method switching
            this.elements.methodSelector.addEventListener('click', (e) => {
                const btn = e.target.closest('.method-btn');
                if (!btn) return;
                
                this.switchMethod(btn.dataset.method);
            });
            
            // Card number formatting & detection
            this.container.addEventListener('input', (e) => {
                if (e.target.id === 'cardNumber') {
                    this.formatCardNumber(e.target);
                    this.detectCard(e.target.value);
                    this.validateAndUpdate();
                }
                if (e.target.id === 'cardExpiry') {
                    this.formatExpiry(e.target);
                    this.validateAndUpdate();
                }
                if (e.target.id === 'cardCvv') {
                    this.validateAndUpdate();
                }
                if (e.target.id === 'bpayBiller' || e.target.id === 'bpayReference') {
                    this.validateAndUpdate();
                }
                if (e.target.id === 'ddBsb') {
                    this.formatBSB(e.target);
                    this.validateAndUpdate();
                }
                if (e.target.id === 'ddAccount' || e.target.id === 'ddName') {
                    this.validateAndUpdate();
                }
            });
            
            // Submit
            this.elements.submitBtn.addEventListener('click', () => this.processPayment());
            
            // Voice
            if (this.options.allowVoiceInput && 'webkitSpeechRecognition' in window) {
                this.elements.voiceBtn.addEventListener('click', () => this.startVoiceInput());
            } else {
                this.elements.voiceBtn.style.display = 'none';
            }
        }
        
        // ---------------------------------------------------------------------
        // METHOD SWITCHING
        // ---------------------------------------------------------------------
        
        switchMethod(method) {
            this.state.setMethod(method);
            
            // Update UI
            this.elements.methodSelector.querySelectorAll('.method-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.method === method);
            });
            
            // Render appropriate form
            const forms = {
                card: this.renderCardForm(),
                bpay: this.renderBPAYForm(),
                directDebit: this.renderDirectDebitForm(),
                payId: this.renderPayIdForm()
            };
            
            this.elements.formArea.innerHTML = forms[method] || forms.card;
            this.elements.formArea.style.animation = 'none';
            this.elements.formArea.offsetHeight; // trigger reflow
            this.elements.formArea.style.animation = 'fadeInUp 0.3s ease-out';
            
            this.validateAndUpdate();
            this.speak(`Switched to ${method} payment. Please enter your details.`);
        }
        
        // ---------------------------------------------------------------------
        // FORMATTING
        // ---------------------------------------------------------------------
        
        formatCardNumber(input) {
            let value = input.value.replace(/\D/g, '');
            const parts = [];
            for (let i = 0; i < value.length; i += 4) {
                parts.push(value.substring(i, i + 4));
            }
            input.value = parts.join(' ');
        }
        
        formatExpiry(input) {
            let value = input.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + ' / ' + value.substring(2, 4);
            }
            input.value = value;
        }
        
        formatBSB(input) {
            let value = input.value.replace(/\D/g, '');
            if (value.length >= 3) {
                value = value.substring(0, 3) + '-' + value.substring(3, 6);
            }
            input.value = value;
        }
        
        // ---------------------------------------------------------------------
        // CARD DETECTION
        // ---------------------------------------------------------------------
        
        detectCard(number) {
            const clean = number.replace(/\D/g, '');
            const type = Utils.detectCardType(clean);
            this.state.setCardType(clean);
            
            const icons = {
                visa: 'VISA',
                mastercard: 'MC',
                amex: 'AMEX',
                diners: 'DIN',
                jcb: 'JCB',
                unionPay: 'UP'
            };
            
            this.elements.cardTypeIcon.textContent = icons[type] || '';
            this.elements.cardTypeIcon.className = 'card-type-icon ' + type;
        }
        
        // ---------------------------------------------------------------------
        // VALIDATION & UPDATE
        // ---------------------------------------------------------------------
        
        validateAndUpdate() {
            const method = this.state.method;
            let validation = { valid: true, errors: [], warnings: [] };
            
            if (method === 'card') {
                const number = this.container.querySelector('#cardNumber')?.value || '';
                const expiry = this.container.querySelector('#cardExpiry')?.value || '';
                const cvv = this.container.querySelector('#cardCvv')?.value || '';
                
                const [month, year] = expiry.split('/').map(s => s.trim());
                validation = ValidationEngine.validateCard(number.replace(/\D/g, ''), month, '20' + year, cvv);
            } else if (method === 'bpay') {
                const biller = this.container.querySelector('#bpayBiller')?.value || '';
                const ref = this.container.querySelector('#bpayReference')?.value || '';
                validation = ValidationEngine.validateBPAY(biller, ref);
            } else if (method === 'directDebit') {
                const bsb = this.container.querySelector('#ddBsb')?.value || '';
                const account = this.container.querySelector('#ddAccount')?.value || '';
                const name = this.container.querySelector('#ddName')?.value || '';
                validation = ValidationEngine.validateDirectDebit(bsb, account, name);
            }
            
            // Amount validation
            const amountValidation = this.state.validate();
            validation.errors = [...validation.errors, ...amountValidation.errors];
            validation.warnings = [...validation.warnings, ...amountValidation.warnings];
            validation.valid = validation.errors.length === 0 && amountValidation.valid;
            
            this.state.errors = validation.errors;
            this.state.warnings = validation.warnings;
            this.state.valid = validation.valid;
            
            this.updateUI(validation);
        }
        
        updateUI(validation) {
            // Update fee display
            const fees = this.state.fees.breakdown;
            this.elements.feeBase.textContent = fees.displayBase || Utils.formatCurrency(this.state.amount);
            this.elements.feeMerchant.textContent = fees.displayFee || '$0.00';
            this.elements.feeGst.textContent = fees.displayGst || '$0.00';
            this.elements.feeTotal.textContent = fees.displayTotal || fees.displayBase;
            
            // Update messages
            const messagesEl = this.elements.messages;
            messagesEl.innerHTML = '';
            
            if (validation.errors.length > 0) {
                validation.errors.forEach(err => {
                    const div = document.createElement('div');
                    div.className = 'message-error';
                    div.textContent = err.message;
                    messagesEl.appendChild(div);
                });
            }
            
            if (validation.warnings.length > 0) {
                validation.warnings.forEach(warn => {
                    const div = document.createElement('div');
                    div.className = 'message-warning';
                    div.textContent = warn.message;
                    messagesEl.appendChild(div);
                });
            }
            
            // Update submit button
            const btn = this.elements.submitBtn;
            const isComplete = this.isFormComplete();
            
            if (validation.valid && isComplete) {
                btn.disabled = false;
                btn.querySelector('.submit-text').textContent = `Pay ${fees.displayTotal || fees.displayBase}`;
            } else {
                btn.disabled = true;
                btn.querySelector('.submit-text').textContent = validation.errors.length > 0 
                    ? 'Fix errors to continue' 
                    : 'Enter payment details';
            }
        }
        
        isFormComplete() {
            const method = this.state.method;
            if (!method) return false;
            
            if (method === 'card') {
                return !!(
                    this.container.querySelector('#cardNumber')?.value &&
                    this.container.querySelector('#cardExpiry')?.value &&
                    this.container.querySelector('#cardCvv')?.value
                );
            }
            if (method === 'bpay') {
                return !!(
                    this.container.querySelector('#bpayBiller')?.value &&
                    this.container.querySelector('#bpayReference')?.value
                );
            }
            if (method === 'directDebit') {
                const auth = this.container.querySelector('#ddAuthority')?.checked;
                return auth && !!(
                    this.container.querySelector('#ddBsb')?.value &&
                    this.container.querySelector('#ddAccount')?.value &&
                    this.container.querySelector('#ddName')?.value
                );
            }
            if (method === 'payId') {
                return !!this.container.querySelector('#payIdValue')?.value;
            }
            
            return false;
        }
        
        // ---------------------------------------------------------------------
        // PAYMENT PROCESSING
        // ---------------------------------------------------------------------
        
        async processPayment() {
            if (!this.state.valid) return;
            
            const btn = this.elements.submitBtn;
            btn.disabled = true;
            btn.querySelector('.submit-text').style.display = 'none';
            btn.querySelector('.submit-loader').style.display = 'flex';
            
            this.state.stage = 'processing';
            this.speak('Processing your payment. Please wait.');
            
            try {
                // Simulate API call
                await this.simulatePayment();
                
                this.state.stage = 'complete';
                this.showSuccess();
                
                if (this.options.onComplete) {
                    this.options.onComplete(this.state.toJSON());
                }
                
            } catch (error) {
                this.state.stage = 'failed';
                this.showError(error.message);
                
                if (this.options.onError) {
                    this.options.onError(error);
                }
            } finally {
                btn.querySelector('.submit-loader').style.display = 'none';
                btn.querySelector('.submit-text').style.display = 'block';
            }
        }
        
        simulatePayment() {
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    // 95% success rate for demo
                    if (Math.random() > 0.05) {
                        resolve({ success: true, transactionId: this.state.transactionId });
                    } else {
                        reject(new Error('Payment declined by issuer. Please try a different card or  Let me continue completing the AI Payment Assistant engine and the Register page with integrated payment widget.

---

## CHUNK 14: `static/js/payment_assistant.js` — AI Payment Engine (Part 2/3)

```javascript
                    } else {
                        reject(new Error('Payment declined by issuer. Please try a different card or contact your bank.'));
                    }
                }, 2000 + Math.random() * 1000);
            });
        }
        
        // ---------------------------------------------------------------------
        // UI STATES
        // ---------------------------------------------------------------------
        
        showSuccess() {
            const fees = this.state.fees.breakdown;
            
            this.elements.formArea.innerHTML = `
                <div class="payment-success">
                    <div class="success-icon">✓</div>
                    <h3 class="success-title">Payment Successful</h3>
                    <p class="success-message">
                        Transaction ID: <strong>${this.state.transactionId}</strong><br>
                        Amount: <strong>${fees.displayTotal}</strong><br>
                        Method: <strong>${this.state.method}</strong>
                    </p>
                    <p class="success-note">
                        A confirmation email has been sent to your registered address. 
                        Our team will contact you within 24 hours to commence your service.
                    </p>
                    <a href="{{ url_for('public.index') }}" class="btn btn-primary">Return to Homepage</a>
                </div>
            `;
            
            this.elements.feeBreakdown.style.display = 'none';
            this.elements.submitBtn.style.display = 'none';
            this.elements.messages.innerHTML = '';
            
            this.speak('Payment successful. Thank you for choosing DGD CONSULT AU.');
        }
        
        showError(message) {
            this.elements.messages.innerHTML = `
                <div class="message-error message-error-critical">
                    <strong>Payment Failed</strong><br>
                    ${message}<br>
                    <button class="btn btn-sm btn-secondary" onclick="location.reload()" style="margin-top: 8px;">
                        Try Again
                    </button>
                </div>
            `;
            
            this.speak('Payment failed. ' + message);
        }
        
        // ---------------------------------------------------------------------
        // VOICE INPUT
        // ---------------------------------------------------------------------
        
        startVoiceInput() {
            if (!('webkitSpeechRecognition' in window)) return;
            
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-AU';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            this.elements.voiceOverlay.style.display = 'flex';
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript.toLowerCase();
                this.processVoiceCommand(transcript);
            };
            
            recognition.onerror = () => {
                this.elements.voiceOverlay.style.display = 'none';
                this.speak('Sorry, I didn\'t catch that. Please try again.');
            };
            
            recognition.onend = () => {
                this.elements.voiceOverlay.style.display = 'none';
            };
            
            recognition.start();
        }
        
        processVoiceCommand(command) {
            // Amount detection
            const amountMatch = command.match(/(\d+)\s*(dollars?|bucks?)/);
            if (amountMatch) {
                const cents = parseInt(amountMatch[1]) * 100;
                this.state.setAmount(cents);
                this.validateAndUpdate();
                this.speak(`Amount set to ${Utils.formatCurrency(cents)}`);
                return;
            }
            
            // Method detection
            if (command.includes('card') || command.includes('credit') || command.includes('debit')) {
                this.switchMethod('card');
            } else if (command.includes('bpay') || command.includes('b-pay')) {
                this.switchMethod('bpay');
            } else if (command.includes('direct debit') || command.includes('bank account')) {
                this.switchMethod('directDebit');
            } else if (command.includes('payid') || command.includes('pay id')) {
                this.switchMethod('payId');
            } else {
                this.speak('I heard: ' + command + '. You can say pay by card, BPAY, direct debit, or PayID.');
            }
        }
        
        // ---------------------------------------------------------------------
        // ACCESSIBILITY — Screen Reader Support
        // ---------------------------------------------------------------------
        
        speak(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-AU';
                utterance.rate = 1.1;
                window.speechSynthesis.speak(utterance);
            }
        }
        
        // ---------------------------------------------------------------------
        // PUBLIC API
        // ---------------------------------------------------------------------
        
        setAmount(amount) {
            this.state.setAmount(amount);
            this.validateAndUpdate();
        }
        
        getState() {
            return this.state.toJSON();
        }
        
        destroy() {
            if (this.container) {
                this.container.innerHTML = '';
            }
        }
    }
    
    // ==========================================================================
    // STATIC MOUNT METHOD
    // ==========================================================================
    
    const AIPaymentAssistant = {
        mount(containerId, options = {}) {
            return new PaymentAssistantInstance(containerId, options);
        },
        
        // Pre-configured presets for common services
        presets: {
            visa_600: { serviceType: 'visa_600', baseAmount: 120000 },
            visa_500: { serviceType: 'visa_500', baseAmount: 200000 },
            consultation: { serviceType: 'consultation', baseAmount: 0 },
            training_rsa: { serviceType: 'training_rsa', baseAmount: 12000 }
        }
    };
    
    // Export to global scope
    global.AIPaymentAssistant = AIPaymentAssistant;
    
})(window);
// ==========================================================================
// DYNAMIC CSS INJECTION
// Appends styles to document head when script loads
// ==========================================================================

(function() {
    const styles = document.createElement('style');
    styles.textContent = `
        /* AI Payment Widget Base */
        .ai-payment-widget {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: white;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 20px 60px rgba(10, 22, 40, 0.12);
            overflow: hidden;
            max-width: 480px;
            margin: 0 auto;
        }
        
        .payment-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            background: linear-gradient(135deg, #0a1628, #1e3a8a);
            color: white;
        }
        
        .payment-service {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .payment-service-icon {
            font-size: 28px;
        }
        
        .payment-service-name {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: rgba(255,255,255,0.7);
        }
        
        .payment-service-amount {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        
        .payment-voice-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        
        .payment-voice-btn:hover {
            background: rgba(255,255,255,0.2);
            transform: scale(1.1);
        }
        
        .payment-body {
            padding: 24px;
        }
        
        /* Method Selector */
        .payment-methods {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 24px;
        }
        
        .method-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            padding: 12px 8px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            background: white;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }
        
        .method-btn:hover {
            border-color: #93c5fd;
            background: #eff6ff;
        }
        
        .method-btn.active {
            border-color: #2563eb;
            background: linear-gradient(135deg, #eff6ff, #dbeafe);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        }
        
        .method-icon {
            font-size: 24px;
        }
        
        .method-label {
            font-size: 11px;
            font-weight: 600;
            color: #475569;
        }
        
        .method-btn.active .method-label {
            color: #1e40af;
        }
        
        /* Form Elements */
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 6px;
        }
        
        .form-input, .form-select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 15px;
            font-family: inherit;
            transition: all 0.2s;
            outline: none;
        }
        
        .form-input:focus, .form-select:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .card-type-icon {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            font-weight: 800;
            color: #64748b;
            padding: 4px 8px;
            background: #f1f5f9;
            border-radius: 6px;
        }
        
        .card-type-icon.visa { color: #1a1f71; }
        .card-type-icon.mastercard { color: #eb001b; }
        .card-type-icon.amex { color: #016fd0; }
        
        .form-row-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        /* BPAY & PayID Displays */
        .bpay-display, .payid-display {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border-radius: 12px;
            margin-bottom: 20px;
        }
        
        .bpay-logo, .payid-logo {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 0.1em;
            color: #0f172a;
            margin-bottom: 8px;
        }
        
        .bpay-instructions, .payid-instructions {
            font-size: 13px;
            color: #64748b;
        }
        
        .bpay-note, .payid-note {
            font-size: 12px;
            color: #64748b;
            padding: 12px;
            background: #fef3c7;
            border-radius: 8px;
            margin-top: 16px;
            line-height: 1.5;
        }
        
        .payid-note {
            background: #dcfce7;
        }
        
        /* Direct Debit */
        .dd-authority {
            padding: 16px;
            background: #f8fafc;
            border-radius: 10px;
            margin-top: 16px;
        }
        
        .checkbox-label {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 13px;
            line-height: 1.5;
            color: #475569;
            cursor: pointer;
        }
        
        .checkbox-label input[type="checkbox"] {
            margin-top: 2px;
            width: 18px;
            height: 18px;
            accent-color: #2563eb;
        }
        
        /* Fee Breakdown */
        .payment-fees {
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            margin: 20px 0;
        }
        
        .fee-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            font-size: 14px;
            color: #64748b;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .fee-row:last-child {
            border-bottom: none;
        }
        
        .fee-total {
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            padding-top: 12px;
            margin-top: 4px;
            border-top: 2px solid #cbd5e1;
        }
        
        /* Messages */
        .payment-messages {
            margin: 16px 0;
        }
        
        .message-error {
            padding: 12px 16px;
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            border-radius: 8px;
            font-size: 13px;
            color: #991b1b;
            margin-bottom: 8px;
        }
        
        .message-warning {
            padding: 12px 16px;
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            border-radius: 8px;
            font-size: 13px;
            color: #92400e;
            margin-bottom: 8px;
        }
        
        .message-error-critical {
            background: #fee2e2;
            border-left-color: #dc2626;
        }
        
        /* Submit Button */
        .payment-submit-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 20px;
        }
        
        .payment-submit-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.4);
        }
        
        .payment-submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: #94a3b8;
        }
        
        .loader-dot {
            width: 8px;
            height: 8px;
            background: white;
            border-radius: 50%;
            animation: loaderBounce 1.4s infinite ease-in-out both;
        }
        
        .loader-dot:nth-child(1) { animation-delay: -0.32s; }
        .loader-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes loaderBounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        /* Security Badges */
        .payment-security {
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }
        
        .security-badge {
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        /* Voice Overlay */
        .voice-overlay {
            position: absolute;
            inset: 0;
            background: rgba(10, 22, 40, 0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
            color: white;
            z-index: 10;
            border-radius: 20px;
        }
        
        .voice-pulse {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #3b82f6;
            animation: voicePulse 1.5s infinite;
        }
        
        @keyframes voicePulse {
            0% { transform: scale(1); opacity: 1; }
            100% { transform: scale(1.5); opacity: 0; }
        }
        
        .voice-text {
            font-size: 18px;
            font-weight: 600;
        }
        
        .voice-hint {
            font-size: 13px;
            color: rgba(255,255,255,0.6);
        }
        
        /* Success State */
        .payment-success {
            text-align: center;
            padding: 40px 20px;
        }
        
        .success-icon {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            color: white;
            margin: 0 auto 20px;
            box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);
        }
        
        .success-title {
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 12px;
        }
        
        .success-message {
            font-size: 14px;
            color: #475569;
            line-height: 1.7;
            margin-bottom: 16px;
        }
        
        .success-note {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 24px;
        }
        
        /* Radio Groups */
        .radio-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .radio-option {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
        }
        
        .radio-option:hover {
            border-color: #93c5fd;
            background: #f8fafc;
        }
        
        .radio-option input[type="radio"] {
            width: 20px;
            height: 20px;
            accent-color: #2563eb;
        }
        
        /* Responsive */
        @media (max-width: 480px) {
            .payment-methods {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .form-row-2 {
                grid-template-columns: 1fr;
            }
            
            .payment-security {
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }
        }
    `;
    
    document.head.appendChild(styles);
})();


