/**
 * uPY 0.2 Client Runtime - Executes uPY AST in JavaScript sandbox
 * 
 * This runs entirely client-side without API calls.
 * Used for state manipulation, conditionals, loops, math in .udos.md
 */

import { type ASTNode, parse, requiresAPI } from './upy-parser';

export interface ExecutionContext {
	variables: Map<string, any>;
	functions: Map<string, { params: string[]; body: ASTNode[] }>;
	state: Record<string, any>;
	output: string[];
}

export interface ExecutionResult {
	success: boolean;
	output: string[];
	state: Record<string, any>;
	error?: string;
	returnValue?: any;
}

/**
 * Client-side uPY runtime
 */
export class ClientUPYRuntime {
	private context: ExecutionContext;
	private maxIterations = 10000; // Prevent infinite loops

	constructor(initialState: Record<string, any> = {}) {
		this.context = {
			variables: new Map(),
			functions: new Map(),
			state: { ...initialState },
			output: []
		};
	}

	/**
	 * Execute uPY source code
	 */
	execute(source: string): ExecutionResult {
		try {
			const ast = parse(source);
			
			// Check if this code requires API
			if (requiresAPI(ast)) {
				return {
					success: false,
					output: [],
					state: this.context.state,
					error: 'This code contains operations that require the API (FILE, MESH, etc.)'
				};
			}

			const result = this.executeNode(ast);
			
			return {
				success: true,
				output: this.context.output,
				state: this.context.state,
				returnValue: result
			};
		} catch (error) {
			return {
				success: false,
				output: this.context.output,
				state: this.context.state,
				error: error instanceof Error ? error.message : String(error)
			};
		}
	}

	/**
	 * Execute a single AST node
	 */
	private executeNode(node: ASTNode): any {
		switch (node.type) {
			case 'Program':
				return this.executeProgram(node);
			case 'SetStatement':
				return this.executeSet(node);
			case 'GetExpression':
				return this.executeGet(node);
			case 'IfStatement':
				return this.executeIf(node);
			case 'ForStatement':
				return this.executeFor(node);
			case 'WhileStatement':
				return this.executeWhile(node);
			case 'FunctionDef':
				return this.executeFunctionDef(node);
			case 'FunctionCall':
				return this.executeFunctionCall(node);
			case 'PrintStatement':
				return this.executePrint(node);
			case 'ReturnStatement':
				return this.executeReturn(node);
			case 'StateGet':
				return this.executeStateGet(node);
			case 'StateSet':
				return this.executeStateSet(node);
			case 'BinaryExpression':
				return this.executeBinary(node);
			case 'UnaryExpression':
				return this.executeUnary(node);
			case 'Literal':
				return node.value;
			case 'Identifier':
				return this.context.variables.get(node.name!) ?? null;
			case 'Command':
				// Commands that reach here are not API-required (filtered earlier)
				// Could be user-defined or no-op
				return null;
			default:
				return null;
		}
	}

	private executeProgram(node: ASTNode): any {
		let result: any = null;
		for (const stmt of node.body || []) {
			result = this.executeNode(stmt);
			// Check for return value
			if (result && typeof result === 'object' && result.__return) {
				return result.value;
			}
		}
		return result;
	}

	private executeSet(node: ASTNode): void {
		const value = node.value ? this.executeNode(node.value as ASTNode) : null;
		this.context.variables.set(node.name!, value);
	}

	private executeGet(node: ASTNode): any {
		return this.context.variables.get(node.name!) ?? null;
	}

	private executeIf(node: ASTNode): any {
		const condition = this.executeNode(node.condition!);
		
		if (this.isTruthy(condition)) {
			for (const stmt of node.body || []) {
				const result = this.executeNode(stmt);
				if (result && typeof result === 'object' && result.__return) {
					return result;
				}
			}
		} else if (node.elseBody) {
			for (const stmt of node.elseBody) {
				const result = this.executeNode(stmt);
				if (result && typeof result === 'object' && result.__return) {
					return result;
				}
			}
		}
		return null;
	}

	private executeFor(node: ASTNode): any {
		const iterable = this.executeNode(node.right!);
		let iterations = 0;
		
		if (Array.isArray(iterable)) {
			for (const item of iterable) {
				if (++iterations > this.maxIterations) {
					throw new Error('Maximum iterations exceeded');
				}
				this.context.variables.set(node.name!, item);
				for (const stmt of node.body || []) {
					const result = this.executeNode(stmt);
					if (result && typeof result === 'object' && result.__return) {
						return result;
					}
				}
			}
		} else if (typeof iterable === 'number') {
			// FOR i IN 10 → iterate 0-9
			for (let i = 0; i < iterable; i++) {
				if (++iterations > this.maxIterations) {
					throw new Error('Maximum iterations exceeded');
				}
				this.context.variables.set(node.name!, i);
				for (const stmt of node.body || []) {
					const result = this.executeNode(stmt);
					if (result && typeof result === 'object' && result.__return) {
						return result;
					}
				}
			}
		}
		return null;
	}

	private executeWhile(node: ASTNode): any {
		let iterations = 0;
		
		while (this.isTruthy(this.executeNode(node.condition!))) {
			if (++iterations > this.maxIterations) {
				throw new Error('Maximum iterations exceeded');
			}
			for (const stmt of node.body || []) {
				const result = this.executeNode(stmt);
				if (result && typeof result === 'object' && result.__return) {
					return result;
				}
			}
		}
		return null;
	}

	private executeFunctionDef(node: ASTNode): void {
		this.context.functions.set(node.name!, {
			params: node.params || [],
			body: node.body || []
		});
	}

	private executeFunctionCall(node: ASTNode): any {
		const func = this.context.functions.get(node.name!);
		if (!func) {
			// Check for built-in functions
			return this.executeBuiltin(node.name!, node.args || []);
		}

		// Create new scope with parameters
		const savedVars = new Map(this.context.variables);
		
		const args = (node.args || []).map(arg => this.executeNode(arg));
		func.params.forEach((param, i) => {
			this.context.variables.set(param, args[i] ?? null);
		});

		let result: any = null;
		for (const stmt of func.body) {
			result = this.executeNode(stmt);
			if (result && typeof result === 'object' && result.__return) {
				result = result.value;
				break;
			}
		}

		// Restore scope
		this.context.variables = savedVars;
		return result;
	}

	private executeBuiltin(name: string, args: ASTNode[]): any {
		const evalArgs = args.map(a => this.executeNode(a));
		
		switch (name.toUpperCase()) {
			case 'LEN':
				return evalArgs[0]?.length ?? 0;
			case 'STR':
				return String(evalArgs[0] ?? '');
			case 'INT':
				return parseInt(String(evalArgs[0] ?? '0'), 10);
			case 'FLOAT':
				return parseFloat(String(evalArgs[0] ?? '0'));
			case 'ABS':
				return Math.abs(evalArgs[0] ?? 0);
			case 'MIN':
				return Math.min(...evalArgs);
			case 'MAX':
				return Math.max(...evalArgs);
			case 'ROUND':
				return Math.round(evalArgs[0] ?? 0);
			case 'FLOOR':
				return Math.floor(evalArgs[0] ?? 0);
			case 'CEIL':
				return Math.ceil(evalArgs[0] ?? 0);
			case 'UPPER':
				return String(evalArgs[0] ?? '').toUpperCase();
			case 'LOWER':
				return String(evalArgs[0] ?? '').toLowerCase();
			case 'TRIM':
				return String(evalArgs[0] ?? '').trim();
			case 'SPLIT':
				return String(evalArgs[0] ?? '').split(evalArgs[1] ?? ' ');
			case 'JOIN':
				return (evalArgs[0] ?? []).join(evalArgs[1] ?? '');
			case 'RANGE':
				const start = evalArgs.length > 1 ? evalArgs[0] : 0;
				const end = evalArgs.length > 1 ? evalArgs[1] : evalArgs[0];
				const step = evalArgs[2] ?? 1;
				const result: number[] = [];
				for (let i = start; i < end; i += step) {
					result.push(i);
				}
				return result;
			case 'NOW':
				return new Date().toISOString();
			case 'DATE':
				return new Date().toISOString().split('T')[0];
			case 'TIME':
				return new Date().toISOString().split('T')[1].split('.')[0];
			default:
				return null;
		}
	}

	private executePrint(node: ASTNode): void {
		const values = (node.args || []).map(arg => this.executeNode(arg));
		const line = values.map(v => this.stringify(v)).join(' ');
		this.context.output.push(line);
	}

	private executeReturn(node: ASTNode): any {
		const value = node.value ? this.executeNode(node.value as ASTNode) : null;
		return { __return: true, value };
	}

	private executeStateGet(node: ASTNode): any {
		const key = (node.args && node.args[0]) ? this.executeNode(node.args[0]) : null;
		if (key === null) return this.context.state;
		
		// Support dot notation: "user.name"
		const parts = String(key).split('.');
		let value: any = this.context.state;
		for (const part of parts) {
			if (value && typeof value === 'object') {
				value = value[part];
			} else {
				return null;
			}
		}
		return value;
	}

	private executeStateSet(node: ASTNode): void {
		if (!node.args || node.args.length < 2) return;
		
		const key = this.executeNode(node.args[0]);
		const value = this.executeNode(node.args[1]);
		
		// Support dot notation: "user.name"
		const parts = String(key).split('.');
		let target: any = this.context.state;
		
		for (let i = 0; i < parts.length - 1; i++) {
			if (!(parts[i] in target)) {
				target[parts[i]] = {};
			}
			target = target[parts[i]];
		}
		
		target[parts[parts.length - 1]] = value;
	}

	private executeBinary(node: ASTNode): any {
		const left = this.executeNode(node.left!);
		const right = this.executeNode(node.right!);
		
		switch (node.operator) {
			case '+':
				if (typeof left === 'string' || typeof right === 'string') {
					return String(left) + String(right);
				}
				return (left ?? 0) + (right ?? 0);
			case '-':
				return (left ?? 0) - (right ?? 0);
			case '*':
				return (left ?? 0) * (right ?? 0);
			case '/':
				return right !== 0 ? (left ?? 0) / right : 0;
			case '%':
				return right !== 0 ? (left ?? 0) % right : 0;
			case '==':
				return left === right;
			case '!=':
				return left !== right;
			case '<':
				return left < right;
			case '>':
				return left > right;
			case '<=':
				return left <= right;
			case '>=':
				return left >= right;
			case 'AND':
				return this.isTruthy(left) && this.isTruthy(right);
			case 'OR':
				return this.isTruthy(left) || this.isTruthy(right);
			default:
				return null;
		}
	}

	private executeUnary(node: ASTNode): any {
		const value = this.executeNode(node.right!);
		
		switch (node.operator) {
			case '-':
				return -(value ?? 0);
			case 'NOT':
				return !this.isTruthy(value);
			default:
				return value;
		}
	}

	private isTruthy(value: any): boolean {
		if (value === null || value === undefined) return false;
		if (typeof value === 'boolean') return value;
		if (typeof value === 'number') return value !== 0;
		if (typeof value === 'string') return value.length > 0;
		if (Array.isArray(value)) return value.length > 0;
		return true;
	}

	private stringify(value: any): string {
		if (value === null || value === undefined) return 'null';
		if (typeof value === 'object') return JSON.stringify(value);
		return String(value);
	}

	/**
	 * Get current state
	 */
	getState(): Record<string, any> {
		return { ...this.context.state };
	}

	/**
	 * Update state
	 */
	setState(state: Record<string, any>): void {
		this.context.state = { ...state };
	}

	/**
	 * Clear output buffer
	 */
	clearOutput(): void {
		this.context.output = [];
	}
}

/**
 * Create a new runtime instance
 */
export function createRuntime(initialState: Record<string, any> = {}): ClientUPYRuntime {
	return new ClientUPYRuntime(initialState);
}
