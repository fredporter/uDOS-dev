// @ts-nocheck
/**
 * uPY 0.2 Parser - Tokenizer and AST builder for client-side execution
 * 
 * Supports:
 * - Variables: SET name = value, GET name
 * - Conditionals: IF/ELSE/ENDIF
 * - Loops: FOR/WHILE/ENDFOR/ENDWHILE
 * - Math: +, -, *, /, %, comparisons
 * - Functions: DEF name(args)/ENDDEF, CALL name(args)
 * - State: STATE.GET, STATE.SET
 */

export type TokenType =
	| 'KEYWORD'
	| 'IDENTIFIER'
	| 'NUMBER'
	| 'STRING'
	| 'OPERATOR'
	| 'PUNCTUATION'
	| 'NEWLINE'
	| 'EOF';

export interface Token {
	type: TokenType;
	value: string;
	line: number;
	column: number;
}

export type ASTNodeType =
	| 'Program'
	| 'SetStatement'
	| 'GetExpression'
	| 'IfStatement'
	| 'ForStatement'
	| 'WhileStatement'
	| 'FunctionDef'
	| 'FunctionCall'
	| 'BinaryExpression'
	| 'UnaryExpression'
	| 'Literal'
	| 'Identifier'
	| 'StateGet'
	| 'StateSet'
	| 'PrintStatement'
	| 'ReturnStatement'
	| 'Command';

export interface ASTNode {
	type: ASTNodeType;
	value?: string | number | boolean | ASTNode;
	name?: string;
	left?: ASTNode;
	right?: ASTNode;
	operator?: string;
	condition?: ASTNode;
	body?: ASTNode[];
	elseBody?: ASTNode[];
	args?: ASTNode[];
	params?: string[];
	module?: string;
	command?: string;
}

// Keywords that indicate API-required operations
export const API_REQUIRED_MODULES = ['FILE', 'MESH', 'KNOWLEDGE', 'BACKUP', 'ARCHIVE', 'TIDY', 'EMAIL'];

const KEYWORDS = new Set([
	'SET', 'GET', 'IF', 'ELSE', 'ENDIF', 'ELSEIF',
	'FOR', 'IN', 'ENDFOR', 'WHILE', 'ENDWHILE',
	'DEF', 'ENDDEF', 'RETURN', 'CALL',
	'STATE', 'PRINT', 'TRUE', 'FALSE', 'NULL',
	'AND', 'OR', 'NOT', 'BREAK', 'CONTINUE'
]);

const OPERATORS = new Set([
	'+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
	'+=', '-=', '*=', '/='
]);

const PUNCTUATION = new Set(['(', ')', '[', ']', '{', '}', ',', '.', ':']);

/**
 * Tokenize uPY source code
 */
export function tokenize(source: string): Token[] {
	const tokens: Token[] = [];
	let pos = 0;
	let line = 1;
	let column = 1;

	while (pos < source.length) {
		const char = source[pos];

		// Skip whitespace (except newlines)
		if (char === ' ' || char === '\t') {
			pos++;
			column++;
			continue;
		}

		// Newlines
		if (char === '\n') {
			tokens.push({ type: 'NEWLINE', value: '\n', line, column });
			pos++;
			line++;
			column = 1;
			continue;
		}

		// Skip carriage returns
		if (char === '\r') {
			pos++;
			continue;
		}

		// Comments (# to end of line)
		if (char === '#') {
			while (pos < source.length && source[pos] !== '\n') {
				pos++;
			}
			continue;
		}

		// Strings
		if (char === '"' || char === "'") {
			const quote = char;
			const start = pos;
			pos++;
			column++;
			
			while (pos < source.length && source[pos] !== quote) {
				if (source[pos] === '\\' && pos + 1 < source.length) {
					pos += 2;
					column += 2;
				} else {
					pos++;
					column++;
				}
			}
			pos++; // Skip closing quote
			column++;
			
			const value = source.slice(start + 1, pos - 1);
			tokens.push({ type: 'STRING', value, line, column: column - value.length - 2 });
			continue;
		}

		// Numbers
		if (/[0-9]/.test(char) || (char === '.' && /[0-9]/.test(source[pos + 1] || ''))) {
			const start = pos;
			while (pos < source.length && /[0-9.]/.test(source[pos])) {
				pos++;
				column++;
			}
			const value = source.slice(start, pos);
			tokens.push({ type: 'NUMBER', value, line, column: column - value.length });
			continue;
		}

		// Multi-char operators
		if (pos + 1 < source.length) {
			const twoChar = source.slice(pos, pos + 2);
			if (OPERATORS.has(twoChar)) {
				tokens.push({ type: 'OPERATOR', value: twoChar, line, column });
				pos += 2;
				column += 2;
				continue;
			}
		}

		// Single-char operators
		if (OPERATORS.has(char)) {
			tokens.push({ type: 'OPERATOR', value: char, line, column });
			pos++;
			column++;
			continue;
		}

		// Punctuation
		if (PUNCTUATION.has(char)) {
			tokens.push({ type: 'PUNCTUATION', value: char, line, column });
			pos++;
			column++;
			continue;
		}

		// Identifiers and keywords
		if (/[a-zA-Z_]/.test(char)) {
			const start = pos;
			while (pos < source.length && /[a-zA-Z0-9_]/.test(source[pos])) {
				pos++;
				column++;
			}
			const value = source.slice(start, pos);
			const type = KEYWORDS.has(value.toUpperCase()) ? 'KEYWORD' : 'IDENTIFIER';
			tokens.push({ type, value: value.toUpperCase(), line, column: column - value.length });
			continue;
		}

		// Unknown character - skip
		pos++;
		column++;
	}

	tokens.push({ type: 'EOF', value: '', line, column });
	return tokens;
}

/**
 * Parse tokens into AST
 */
export class Parser {
	private tokens: Token[];
	private pos: number = 0;

	constructor(tokens: Token[]) {
		this.tokens = tokens.filter(t => t.type !== 'NEWLINE'); // Simplify by removing newlines
	}

	private current(): Token {
		return this.tokens[this.pos] || { type: 'EOF', value: '', line: 0, column: 0 };
	}

	private peek(offset: number = 1): Token {
		return this.tokens[this.pos + offset] || { type: 'EOF', value: '', line: 0, column: 0 };
	}

	private advance(): Token {
		return this.tokens[this.pos++];
	}

	private expect(type: TokenType, value?: string): Token {
		const token = this.current();
		if (token.type !== type || (value && token.value !== value)) {
			throw new Error(`Expected ${type} ${value || ''}, got ${token.type} ${token.value} at line ${token.line}`);
		}
		return this.advance();
	}

	parse(): ASTNode {
		const body: ASTNode[] = [];
		
		while (this.current().type !== 'EOF') {
			const stmt = this.parseStatement();
			if (stmt) body.push(stmt);
		}

		return { type: 'Program', body };
	}

	private parseStatement(): ASTNode | null {
		const token = this.current();

		switch (token.value) {
			case 'SET':
				return this.parseSetStatement();
			case 'IF':
				return this.parseIfStatement();
			case 'FOR':
				return this.parseForStatement();
			case 'WHILE':
				return this.parseWhileStatement();
			case 'DEF':
				return this.parseFunctionDef();
			case 'PRINT':
				return this.parsePrintStatement();
			case 'RETURN':
				return this.parseReturnStatement();
			case 'STATE':
				return this.parseStateOperation();
			default:
				// Could be a command (MODULE.ACTION) or function call
				if (token.type === 'IDENTIFIER') {
					return this.parseCommandOrCall();
				}
				this.advance(); // Skip unknown
				return null;
		}
	}

	private parseSetStatement(): ASTNode {
		this.advance(); // Skip SET
		const name = this.expect('IDENTIFIER').value;
		this.expect('OPERATOR', '=');
		const value = this.parseExpression();
		return { type: 'SetStatement', name, value };
	}

	private parseIfStatement(): ASTNode {
		this.advance(); // Skip IF
		const condition = this.parseExpression();
		const body: ASTNode[] = [];
		let elseBody: ASTNode[] | undefined;

		while (this.current().value !== 'ENDIF' && this.current().value !== 'ELSE' && this.current().value !== 'ELSEIF' && this.current().type !== 'EOF') {
			const stmt = this.parseStatement();
			if (stmt) body.push(stmt);
		}

		if (this.current().value === 'ELSE') {
			this.advance();
			elseBody = [];
			while (this.current().value !== 'ENDIF' && this.current().type !== 'EOF') {
				const stmt = this.parseStatement();
				if (stmt) elseBody.push(stmt);
			}
		}

		if (this.current().value === 'ENDIF') {
			this.advance();
		}

		return { type: 'IfStatement', condition, body, elseBody };
	}

	private parseForStatement(): ASTNode {
		this.advance(); // Skip FOR
		const name = this.expect('IDENTIFIER').value;
		this.expect('KEYWORD', 'IN');
		const right = this.parseExpression();
		const body: ASTNode[] = [];

		while (this.current().value !== 'ENDFOR' && this.current().type !== 'EOF') {
			const stmt = this.parseStatement();
			if (stmt) body.push(stmt);
		}

		if (this.current().value === 'ENDFOR') {
			this.advance();
		}

		return { type: 'ForStatement', name, right, body };
	}

	private parseWhileStatement(): ASTNode {
		this.advance(); // Skip WHILE
		const condition = this.parseExpression();
		const body: ASTNode[] = [];

		while (this.current().value !== 'ENDWHILE' && this.current().type !== 'EOF') {
			const stmt = this.parseStatement();
			if (stmt) body.push(stmt);
		}

		if (this.current().value === 'ENDWHILE') {
			this.advance();
		}

		return { type: 'WhileStatement', condition, body };
	}

	private parseFunctionDef(): ASTNode {
		this.advance(); // Skip DEF
		const name = this.expect('IDENTIFIER').value;
		this.expect('PUNCTUATION', '(');
		
		const params: string[] = [];
		while (this.current().value !== ')') {
			if (params.length > 0) {
				this.expect('PUNCTUATION', ',');
			}
			params.push(this.expect('IDENTIFIER').value);
		}
		this.expect('PUNCTUATION', ')');

		const body: ASTNode[] = [];
		while (this.current().value !== 'ENDDEF' && this.current().type !== 'EOF') {
			const stmt = this.parseStatement();
			if (stmt) body.push(stmt);
		}

		if (this.current().value === 'ENDDEF') {
			this.advance();
		}

		return { type: 'FunctionDef', name, params, body };
	}

	private parsePrintStatement(): ASTNode {
		this.advance(); // Skip PRINT
		const args: ASTNode[] = [this.parseExpression()];
		return { type: 'PrintStatement', args };
	}

	private parseReturnStatement(): ASTNode {
		this.advance(); // Skip RETURN
		const value = this.parseExpression();
		return { type: 'ReturnStatement', value };
	}

	private parseStateOperation(): ASTNode {
		this.advance(); // Skip STATE
		this.expect('PUNCTUATION', '.');
		const operation = this.expect('IDENTIFIER').value;
		
		this.expect('PUNCTUATION', '(');
		const args: ASTNode[] = [];
		while (this.current().value !== ')') {
			if (args.length > 0) {
				this.expect('PUNCTUATION', ',');
			}
			args.push(this.parseExpression());
		}
		this.expect('PUNCTUATION', ')');

		return {
			type: operation === 'GET' ? 'StateGet' : 'StateSet',
			args
		};
	}

	private parseCommandOrCall(): ASTNode {
		const name = this.advance().value;
		
		// Check for module.command pattern (e.g., FILE.READ)
		if (this.current().value === '.') {
			this.advance(); // Skip .
			const command = this.expect('IDENTIFIER').value;
			
			// Parse arguments if present
			const args: ASTNode[] = [];
			if (this.current().value === '(') {
				this.advance();
				while (this.current().value !== ')' && this.current().type !== 'EOF') {
					if (args.length > 0) {
						this.expect('PUNCTUATION', ',');
					}
					args.push(this.parseExpression());
				}
				if (this.current().value === ')') this.advance();
			}

			return { type: 'Command', module: name, command, args };
		}

		// Function call
		if (this.current().value === '(') {
			this.advance();
			const args: ASTNode[] = [];
			while (this.current().value !== ')' && this.current().type !== 'EOF') {
				if (args.length > 0) {
					this.expect('PUNCTUATION', ',');
				}
				args.push(this.parseExpression());
			}
			if (this.current().value === ')') this.advance();
			
			return { type: 'FunctionCall', name, args };
		}

		// Just an identifier reference
		return { type: 'Identifier', name };
	}

	private parseExpression(): ASTNode {
		return this.parseOr();
	}

	private parseOr(): ASTNode {
		let left = this.parseAnd();
		
		while (this.current().value === 'OR') {
			const operator = this.advance().value;
			const right = this.parseAnd();
			left = { type: 'BinaryExpression', operator, left, right };
		}
		
		return left;
	}

	private parseAnd(): ASTNode {
		let left = this.parseComparison();
		
		while (this.current().value === 'AND') {
			const operator = this.advance().value;
			const right = this.parseComparison();
			left = { type: 'BinaryExpression', operator, left, right };
		}
		
		return left;
	}

	private parseComparison(): ASTNode {
		let left = this.parseAdditive();
		
		while (['==', '!=', '<', '>', '<=', '>='].includes(this.current().value)) {
			const operator = this.advance().value;
			const right = this.parseAdditive();
			left = { type: 'BinaryExpression', operator, left, right };
		}
		
		return left;
	}

	private parseAdditive(): ASTNode {
		let left = this.parseMultiplicative();
		
		while (['+', '-'].includes(this.current().value)) {
			const operator = this.advance().value;
			const right = this.parseMultiplicative();
			left = { type: 'BinaryExpression', operator, left, right };
		}
		
		return left;
	}

	private parseMultiplicative(): ASTNode {
		let left = this.parseUnary();
		
		while (['*', '/', '%'].includes(this.current().value)) {
			const operator = this.advance().value;
			const right = this.parseUnary();
			left = { type: 'BinaryExpression', operator, left, right };
		}
		
		return left;
	}

	private parseUnary(): ASTNode {
		if (this.current().value === 'NOT' || this.current().value === '-') {
			const operator = this.advance().value;
			const right = this.parseUnary();
			return { type: 'UnaryExpression', operator, right };
		}
		
		return this.parsePrimary();
	}

	private parsePrimary(): ASTNode {
		const token = this.current();

		// Literals
		if (token.type === 'NUMBER') {
			this.advance();
			return { type: 'Literal', value: parseFloat(token.value) };
		}

		if (token.type === 'STRING') {
			this.advance();
			return { type: 'Literal', value: token.value };
		}

		if (token.value === 'TRUE') {
			this.advance();
			return { type: 'Literal', value: true };
		}

		if (token.value === 'FALSE') {
			this.advance();
			return { type: 'Literal', value: false };
		}

		if (token.value === 'NULL') {
			this.advance();
			return { type: 'Literal', value: null };
		}

		// Parenthesized expression
		if (token.value === '(') {
			this.advance();
			const expr = this.parseExpression();
			this.expect('PUNCTUATION', ')');
			return expr;
		}

		// GET variable
		if (token.value === 'GET') {
			this.advance();
			const name = this.expect('IDENTIFIER').value;
			return { type: 'GetExpression', name };
		}

		// STATE.GET
		if (token.value === 'STATE') {
			return this.parseStateOperation();
		}

		// Identifier or command
		if (token.type === 'IDENTIFIER') {
			return this.parseCommandOrCall();
		}

		// Default: return null literal
		this.advance();
		return { type: 'Literal', value: null };
	}
}

/**
 * Parse uPY source code into AST
 */
export function parse(source: string): ASTNode {
	const tokens = tokenize(source);
	const parser = new Parser(tokens);
	return parser.parse();
}

/**
 * Check if AST contains operations requiring API
 */
export function requiresAPI(ast: ASTNode): boolean {
	if (ast.type === 'Command' && ast.module && API_REQUIRED_MODULES.includes(ast.module)) {
		return true;
	}

	// Check children
	if (ast.body) {
		for (const child of ast.body) {
			if (requiresAPI(child)) return true;
		}
	}
	if (ast.elseBody) {
		for (const child of ast.elseBody) {
			if (requiresAPI(child)) return true;
		}
	}
	if (ast.left && requiresAPI(ast.left)) return true;
	if (ast.right && requiresAPI(ast.right)) return true;
	if (ast.condition && requiresAPI(ast.condition)) return true;
	if (ast.value && typeof ast.value === 'object' && requiresAPI(ast.value as ASTNode)) return true;
	if (ast.args) {
		for (const arg of ast.args) {
			if (requiresAPI(arg)) return true;
		}
	}

	return false;
}
