class Environment {

	public mappings: [{ name: any, meaning: any }];
	constructor(public parent?: Environment) {}

	find<T>(what: T, test: (obj: T) => boolean = (obj) => obj == what): any {
		const meaning = this.mappings.find(mapping => test(mapping.name));
		if(meaning) {
			return meaning;
		} else if(this.parent) {
			return this.parent.find(what, test);
		} else {
			return undefined;
		}
	}

}