import React from 'react';
import { Plus, X, ChevronDown, ChevronRight } from 'lucide-react';

const typeColors = {
  string: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  integer: 'bg-green-500/20 text-green-300 border-green-500/30',
  number: 'bg-green-500/20 text-green-300 border-green-500/30',
  boolean: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  array: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  object: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
};

export const CustomFieldTemplate = (props) => {
  const { id, classNames, label, help, required, description, errors, children, schema } = props;
  
  // RJSF passes a lot of things. If it's an object/array, we just render children directly 
  // because the Object/Array templates will handle their own layout.
  if (schema.type === 'object' || schema.type === 'array') {
    return (
      <div className={classNames}>
        {children}
        {errors}
        {help}
      </div>
    );
  }

  const typeBadge = schema.type ? (
    <span className={`ml-2 px-1.5 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider border ${typeColors[schema.type] || 'bg-gray-500/20 text-gray-300 border-gray-500/30'}`}>
      {schema.type}
    </span>
  ) : null;

  return (
    <div className={`form-group flex flex-col sm:flex-row sm:items-start mb-5 group ${classNames}`}>
      <div className="sm:w-1/3 pr-4 pt-2 mb-1 sm:mb-0 flex flex-col justify-start">
        <label htmlFor={id} className="flex flex-wrap items-center text-sm font-medium text-[var(--color-text-main)] group-focus-within:text-[var(--color-primary)] transition-colors leading-tight">
          {label}
          {typeBadge}
          {required && <span className="text-red-500 ml-1" title="Required">*</span>}
        </label>
      </div>
      <div className="sm:w-2/3 relative flex-1">
        {children}
        {!required && (
          <span className="absolute right-3 top-2.5 text-xs text-gray-500 pointer-events-none opacity-50">
            optional
          </span>
        )}
        {description && (
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1.5 ml-1 leading-snug">
            {description}
          </div>
        )}
        {errors}
        {help}
      </div>
    </div>
  );
};

export const CustomObjectFieldTemplate = (props) => {
  const { title, properties, required, description, uiSchema, idSchema } = props;
  
  // Root doesn't need indentation
  const isRoot = idSchema && idSchema.$id === "root";
  
  return (
    <div className={`${!isRoot ? 'ml-4 pl-4 border-l-2 border-[var(--color-border)] focus-within:border-[var(--color-primary)] transition-colors' : ''}`}>
      {title && !isRoot && (
        <h3 className="text-md font-semibold text-[var(--color-text-main)] mb-3">
          {title}
        </h3>
      )}
      {description && <p className="text-xs text-[var(--color-text-muted)] mb-3">{description}</p>}
      <div className="space-y-2">
        {properties.map(element => (
          <div key={element.content.key} className="object-property">
            {element.content}
          </div>
        ))}
      </div>
    </div>
  );
};

export const CustomArrayFieldTemplate = (props) => {
  const { title, items, canAdd, onAddClick, required, schema } = props;
  
  return (
    <div className="mb-6">
      {title && (
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-md font-semibold text-[var(--color-text-main)]">
            {title}
            {required && <span className="text-red-500 ml-1">*</span>}
          </h3>
        </div>
      )}
      
      <div className="space-y-3">
        {items.map(element => (
          <div key={element.key} className="relative bg-[rgba(255,255,255,0.02)] border border-[var(--color-border)] focus-within:border-[var(--color-primary)] focus-within:bg-[rgba(167,139,250,0.02)] rounded-lg p-4 pt-6 transition-all group/item">
            {element.hasRemove && (
              <button 
                type="button" 
                onClick={element.onDropIndexClick(element.index)}
                className="absolute top-2 right-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 p-1 rounded transition-colors"
                title="Remove"
              >
                <X size={16} />
              </button>
            )}
            {element.children}
          </div>
        ))}
      </div>
      
      {canAdd && (
        <button 
          type="button"
          onClick={onAddClick}
          className="mt-3 flex items-center justify-center gap-2 w-full py-2 px-4 rounded-md border border-dashed border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:border-[var(--color-primary)] hover:bg-[rgba(167,139,250,0.05)] transition-all"
        >
          <Plus size={16} />
          Add {title || 'Item'}
        </button>
      )}
    </div>
  );
};
